from django.db import migrations


def remove_stale_contenttypes(apps, schema_editor):
    """Remove stale ContentTypes for deleted models"""
    ContentType = apps.get_model('contenttypes', 'ContentType')
    # Remove ReportIssue ContentType
    ContentType.objects.filter(app_label='orders', model='reportissue').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0041_remove_orphaned_reportissue_table'),
    ]

    operations = [
        migrations.RunPython(remove_stale_contenttypes, migrations.RunPython.noop),
    ]
