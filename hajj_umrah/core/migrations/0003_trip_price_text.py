from django.db import migrations, models


def convert_null_price(apps, schema_editor):
    Trip = apps.get_model('core', 'Trip')
    Trip.objects.filter(price__isnull=True).update(price='')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_seed_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trip',
            name='price',
            field=models.CharField(
                blank=True,
                help_text='اتركه فارغاً لعرض «اكتب لنا»، أو اكتب نصاً حراً مثل «السعر قريباً».',
                max_length=100,
                verbose_name='السعر',
            ),
        ),
        migrations.RunPython(convert_null_price, migrations.RunPython.noop),
    ]