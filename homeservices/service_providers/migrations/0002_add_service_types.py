from django.db import migrations

def add_service_types(apps, schema_editor):
    ServiceType = apps.get_model('service_providers', 'ServiceType')
    service_types = [
        {
            'name': 'Cleaning',
            'description': 'Professional home cleaning services including deep cleaning, regular maintenance, and specialized cleaning tasks.'
        },
        {
            'name': 'Painting',
            'description': 'Interior and exterior painting services with expert color consultation and quality finishes.'
        },
        {
            'name': 'Roofing',
            'description': 'Roof repair, maintenance, and installation services by certified professionals.'
        },
        {
            'name': 'Electrical',
            'description': 'Licensed electrical services including installations, repairs, and maintenance work.'
        },
        {
            'name': 'Flooring',
            'description': 'Installation and repair of various flooring types including hardwood, tile, and laminate.'
        },
        {
            'name': 'Plastering',
            'description': 'Professional plastering services for walls and ceilings, including repairs and new installations.'
        },
        {
            'name': 'Plumbing',
            'description': 'Comprehensive plumbing services including repairs, installations, and maintenance.'
        },
        {
            'name': 'Appliance Repair',
            'description': 'Repair and maintenance services for home appliances including refrigerators, washers, and dryers.'
        }
    ]
    
    for service_type in service_types:
        ServiceType.objects.create(**service_type)

def remove_service_types(apps, schema_editor):
    ServiceType = apps.get_model('service_providers', 'ServiceType')
    ServiceType.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('service_providers', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_service_types, remove_service_types),
    ] 