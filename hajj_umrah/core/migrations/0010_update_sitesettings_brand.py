from django.db import migrations


def update_brand(apps, schema_editor):
    SiteSettings = apps.get_model('core', 'SiteSettings')
    SiteSettings.objects.filter(pk=1).update(
        company='الطوخي فلاي',
        hero_title='رحلتك الروحانية تبدأ من هنا',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_alter_sitesettings_company_and_more'),
    ]

    operations = [
        migrations.RunPython(update_brand, migrations.RunPython.noop),
    ]