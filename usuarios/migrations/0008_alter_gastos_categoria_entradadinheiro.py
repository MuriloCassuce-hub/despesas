# Generated by Django 5.0.7 on 2024-10-08 15:29

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0007_gastos_parcelado'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gastos',
            name='categoria',
            field=models.CharField(choices=[('Alimentação', 'Alimentação'), ('Transporte', 'Transporte'), ('Entretenimento', 'Entretenimento'), ('Moradia', 'Moradia'), ('Lazer', 'Lazer'), ('Educação', 'Educação'), ('Serviços', 'Serviços'), ('Saúde', 'Saúde'), ('Outros', 'Outros')], max_length=30),
        ),
        migrations.CreateModel(
            name='EntradaDinheiro',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valor_de_entrada', models.DecimalField(decimal_places=2, max_digits=1000000)),
                ('saldo_anterior', models.DecimalField(decimal_places=2, max_digits=1000000)),
                ('DataEntradaSaldo', models.CharField(max_length=7)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]