from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
        ('locations', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='userlocation',
                    name='accuracy',
                    field=models.FloatField(blank=True, null=True),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_schema = 'public'
                              AND table_name = 'locations_userlocation'
                              AND column_name = 'accuracy'
                        ) THEN
                            ALTER TABLE "locations_userlocation"
                                ADD COLUMN "accuracy" double precision NULL;
                        END IF;
                    END $$;
                    """,
                    reverse_sql='ALTER TABLE "locations_userlocation" DROP COLUMN IF EXISTS "accuracy";',
                ),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='userlocation',
                    name='heading',
                    field=models.FloatField(blank=True, null=True),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_schema = 'public'
                              AND table_name = 'locations_userlocation'
                              AND column_name = 'heading'
                        ) THEN
                            ALTER TABLE "locations_userlocation"
                                ADD COLUMN "heading" double precision NULL;
                        END IF;
                    END $$;
                    """,
                    reverse_sql='ALTER TABLE "locations_userlocation" DROP COLUMN IF EXISTS "heading";',
                ),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='userlocation',
                    name='speed',
                    field=models.FloatField(blank=True, null=True),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_schema = 'public'
                              AND table_name = 'locations_userlocation'
                              AND column_name = 'speed'
                        ) THEN
                            ALTER TABLE "locations_userlocation"
                                ADD COLUMN "speed" double precision NULL;
                        END IF;
                    END $$;
                    """,
                    reverse_sql='ALTER TABLE "locations_userlocation" DROP COLUMN IF EXISTS "speed";',
                ),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='Waypoint',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('name', models.CharField(max_length=255)),
                        ('description', models.TextField(blank=True, null=True)),
                        ('latitude', models.FloatField()),
                        ('longitude', models.FloatField()),
                        ('address', models.CharField(max_length=255)),
                        ('waypoint_type', models.CharField(choices=[('pickup', 'Pickup'), ('delivery', 'Delivery'), ('stop', 'Stop'), ('checkpoint', 'Checkpoint')], max_length=20)),
                        ('order_index', models.IntegerField(default=0)),
                        ('is_visited', models.BooleanField(default=False)),
                        ('visited_at', models.DateTimeField(blank=True, null=True)),
                        ('estimated_arrival_time', models.DateTimeField(blank=True, null=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('order', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='waypoints', to='orders.order')),
                    ],
                    options={
                        'ordering': ['order_index'],
                    },
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1
                            FROM information_schema.tables
                            WHERE table_schema = 'public'
                              AND table_name = 'locations_waypoint'
                        ) THEN
                            CREATE TABLE "locations_waypoint" (
                                "id" bigserial NOT NULL PRIMARY KEY,
                                "name" varchar(255) NOT NULL,
                                "description" text NULL,
                                "latitude" double precision NOT NULL,
                                "longitude" double precision NOT NULL,
                                "address" varchar(255) NOT NULL,
                                "waypoint_type" varchar(20) NOT NULL,
                                "order_index" integer NOT NULL DEFAULT 0,
                                "is_visited" boolean NOT NULL DEFAULT FALSE,
                                "visited_at" timestamp with time zone NULL,
                                "estimated_arrival_time" timestamp with time zone NULL,
                                "created_at" timestamp with time zone NOT NULL,
                                "updated_at" timestamp with time zone NOT NULL,
                                "order_id" bigint NULL REFERENCES "orders_order"("id") DEFERRABLE INITIALLY DEFERRED,
                                CONSTRAINT "locations_waypoint_order_index_cdf2fb12" CHECK ("waypoint_type" in ('pickup','delivery','stop','checkpoint'))
                            );
                        END IF;
                    END $$;
                    """,
                    reverse_sql='DROP TABLE IF EXISTS "locations_waypoint" CASCADE;',
                ),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='RouteCalculation',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('distance', models.FloatField(help_text='Distance in kilometers')),
                        ('duration', models.IntegerField(help_text='Estimated duration in seconds')),
                        ('route_data', models.JSONField(blank=True, help_text='Encoded route data', null=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('end_waypoint', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='routes_as_end', to='locations.waypoint')),
                        ('order', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='routes', to='orders.order')),
                        ('start_waypoint', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='routes_as_start', to='locations.waypoint')),
                    ],
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1
                            FROM information_schema.tables
                            WHERE table_schema = 'public'
                              AND table_name = 'locations_routecalculation'
                        ) THEN
                            CREATE TABLE "locations_routecalculation" (
                                "id" bigserial NOT NULL PRIMARY KEY,
                                "distance" double precision NOT NULL,
                                "duration" integer NOT NULL,
                                "route_data" jsonb NULL,
                                "created_at" timestamp with time zone NOT NULL,
                                "end_waypoint_id" bigint NOT NULL REFERENCES "locations_waypoint"("id") DEFERRABLE INITIALLY DEFERRED,
                                "order_id" bigint NULL REFERENCES "orders_order"("id") DEFERRABLE INITIALLY DEFERRED,
                                "start_waypoint_id" bigint NOT NULL REFERENCES "locations_waypoint"("id") DEFERRABLE INITIALLY DEFERRED
                            );
                        END IF;
                    END $$;
                    """,
                    reverse_sql='DROP TABLE IF EXISTS "locations_routecalculation" CASCADE;',
                ),
            ],
        ),
    ]