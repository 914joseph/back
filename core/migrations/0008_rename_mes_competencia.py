# Generated manually to rename column

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_avaliacaodesempenho_mescompetencia'),
    ]

    operations = [
        migrations.RenameField(
            model_name='avaliacaodesempenho',
            old_name='mesCompetencia',
            new_name='mes_competencia',
        ),
    ]
