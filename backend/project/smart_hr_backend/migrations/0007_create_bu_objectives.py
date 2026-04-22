# Generated migration for BU Objectives

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('smart_hr_backend', '0006_alter_buobjective_unique_together'),
    ]

    operations = [
        # Create OrgUnit model
        migrations.CreateModel(
            name='OrgUnit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=100, unique=True)),
                ('name', models.CharField(max_length=150, unique=True)),
                ('sheet_name', models.CharField(max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        
        # Remove old BUObjective if it exists and create new one
        migrations.DeleteModel(
            name='BUObjective',
        ),
        
        migrations.CreateModel(
            name='BUObjective',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('parameter_name', models.CharField(blank=True, max_length=255, null=True)),
                ('goal_text', models.TextField()),
                ('measure_of_success', models.TextField(blank=True, null=True)),
                ('linkage_ta_raw', models.TextField(blank=True, null=True)),
                ('linkage_go_raw', models.TextField(blank=True, null=True)),
                ('source_sheet', models.CharField(max_length=200)),
                ('source_row_no', models.IntegerField(blank=True, null=True)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('org_unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='objectives', to='smart_hr_backend.orgunit')),
            ],
            options={
                'ordering': ['org_unit__name', 'source_row_no', 'id'],
            },
        ),
        
        # Create BUObjectiveTALink
        migrations.CreateModel(
            name='BUObjectiveTALink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ta_code_raw', models.CharField(max_length=100)),
                ('ta_code_normalized', models.CharField(db_index=True, max_length=50)),
                ('objective', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ta_links', to='smart_hr_backend.buobjective')),
            ],
            options={
                'ordering': ['ta_code_normalized'],
            },
        ),
        
        # Create BUObjectiveGOLink
        migrations.CreateModel(
            name='BUObjectiveGOLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('go_code_raw', models.CharField(max_length=100)),
                ('go_code_normalized', models.CharField(db_index=True, max_length=50)),
                ('objective', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='go_links', to='smart_hr_backend.buobjective')),
            ],
            options={
                'ordering': ['go_code_normalized'],
            },
        ),
    ]
