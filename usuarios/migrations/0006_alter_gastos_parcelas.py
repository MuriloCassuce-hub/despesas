# Generated by Django 5.0.7 on 2024-09-19 02:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0005_alter_gastos_usuario'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gastos',
            name='parcelas',
            field=models.CharField(max_length=6),
        ),
    ]