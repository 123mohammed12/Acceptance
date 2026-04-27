import os
import django
import json
from django.core import serializers

# ضبط الإعدادات
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

def export_to_json():
    output_path = r'e:\my_projecters\Acceptance_Backend_Production\data.json'
    print(f"جاري تصدير البيانات إلى: {output_path} ...")
    
    # تصدير موديلات تطبيق my_acceptance فقط
    from django.apps import apps
    my_app = apps.get_app_config('my_acceptance')
    models = my_app.get_models()
    
    all_objects = []
    for model in models:
        all_objects.extend(model.objects.all())
        
    data = serializers.serialize('json', all_objects, indent=2)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(data)
        
    print("✅ تم تصدير البيانات بنجاح!")

if __name__ == '__main__':
    export_to_json()
