import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from my_acceptance.models import University, College

def run():
    sanaa_uni = University.objects.filter(name__contains='صنعاء').first()
    if not sanaa_uni:
        print("❌ لم يتم العثور على جامعة صنعاء في النظام.")
        return

    sanaa_colleges = sanaa_uni.colleges.all()
    if not sanaa_colleges:
        print("❌ جامعة صنعاء لا تمتلك أي كليات حالياً.")
        return

    other_unis = University.objects.exclude(id=sanaa_uni.id)
    if not other_unis:
        print("❌ لا توجد جامعات أخرى لنقل الكليات إليها.")
        return

    print(f"✅ سيتم نسخ {sanaa_colleges.count()} كليات من {sanaa_uni.name} إلى {other_unis.count()} جامعات أخرى.")
    count = 0

    for uni in other_unis:
        for college in sanaa_colleges:
            # التحقق مما إذا كانت الكلية موجودة مسبقاً بنفس الرمز
            existing = College.objects.filter(university=uni, code=college.code).first()
            if not existing:
                new_college = College.objects.create(
                    university=uni,
                    name=college.name,
                    code=college.code,
                    category=college.category,
                    icon_name=college.icon_name,
                    high_school_weight=college.high_school_weight,
                    exam_weight=college.exam_weight,
                    is_active=college.is_active
                )
                # نسخ الارتباطات مع المواد (مقررات القبول)
                new_college.subjects.set(college.subjects.all())
                count += 1
            else:
                # تحديث المواد فقط للكلية الموجودة لضمان التزامن
                existing.subjects.add(*college.subjects.all())
                
    print(f"🎉 تمت العملية بنجاح. تم استنساخ/تحديث {count} كليات وتوزيعها مع موادها على باقي الجامعات.")

if __name__ == '__main__':
    run()
