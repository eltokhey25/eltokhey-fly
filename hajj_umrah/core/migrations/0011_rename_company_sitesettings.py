from django.db import migrations, models


def update_company(apps, schema_editor):
    SiteSettings = apps.get_model('core', 'SiteSettings')
    SiteSettings.objects.filter(pk=1).update(company='الطوخي للحج والعمرة')


def reverse_company(apps, schema_editor):
    SiteSettings = apps.get_model('core', 'SiteSettings')
    SiteSettings.objects.filter(pk=1).update(company='الطوخي فلاي')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_update_sitesettings_brand'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitesettings',
            name='company',
            field=models.CharField(default='الطوخي للحج والعمرة', max_length=255, verbose_name='اسم الشركة'),
        ),
        migrations.RunPython(update_company, reverse_company),
    ]