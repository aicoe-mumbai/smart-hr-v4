# Generated migration to remove old BU-related models

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('smart_hr_backend', '0002_gapanalysisrecord'),
    ]

    operations = [
        # Remove link tables first (foreign key dependencies)
        migrations.DeleteModel(
            name='BUObjectiveGOLink',
        ),
        migrations.DeleteModel(
            name='BUObjectiveTALink',
        ),
        # Remove main tables
        migrations.DeleteModel(
            name='BUObjective',
        ),
        migrations.DeleteModel(
            name='OrgUnit',
        ),
        migrations.DeleteModel(
            name='ThrustArea',
        ),
        migrations.DeleteModel(
            name='GroupObjective',
        ),
    ]
