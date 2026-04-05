from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0021_alter_ordertype_base_price_alter_ordertype_min_price_and_more"),
    ]

    operations = [
        # Try to create pg_trgm extension safely (ignore if not installed)
        migrations.RunSQL(
            sql=(
                "DO $$\n"
                "BEGIN\n"
                "  BEGIN\n"
                "    EXECUTE 'CREATE EXTENSION IF NOT EXISTS pg_trgm';\n"
                "  EXCEPTION WHEN undefined_file THEN\n"
                "    NULL;\n"
                "  END;\n"
                "END;\n"
                "$$;"
            ),
            reverse_sql=(
                "DO $$\n"
                "BEGIN\n"
                "  BEGIN\n"
                "    EXECUTE 'DROP EXTENSION IF EXISTS pg_trgm';\n"
                "  EXCEPTION WHEN undefined_object THEN\n"
                "    NULL;\n"
                "  END;\n"
                "END;\n"
                "$$;"
            ),
        ),
        # Conditionally create the trigram GIN index only if pg_trgm exists; otherwise no-op
        migrations.RunSQL(
            sql=(
                "DO $$\n"
                "BEGIN\n"
                "  IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm') THEN\n"
                "    IF NOT EXISTS (\n"
                "      SELECT 1 FROM pg_class c\n"
                "      JOIN pg_namespace n ON n.oid = c.relnamespace\n"
                "      WHERE c.relkind = 'i' AND c.relname = 'idx_title_trgm'\n"
                "    ) THEN\n"
                "      EXECUTE 'CREATE INDEX idx_title_trgm ON orders_order USING GIN (title gin_trgm_ops)';\n"
                "    END IF;\n"
                "  END IF;\n"
                "END;\n"
                "$$;"
            ),
            reverse_sql=(
                "DO $$\n"
                "BEGIN\n"
                "  IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_title_trgm') THEN\n"
                "    EXECUTE 'DROP INDEX IF EXISTS idx_title_trgm';\n"
                "  END IF;\n"
                "END;\n"
                "$$;"
            ),
        ),
    ]