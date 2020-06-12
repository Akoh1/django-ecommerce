# Generated by Django 2.2 on 2020-04-12 19:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_billingaddress'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='bill_address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.BillingAddress'),
        ),
    ]