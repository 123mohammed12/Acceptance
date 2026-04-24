import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from my_acceptance.models import University, College, Subject, Question, Option

class Command(BaseCommand):
    help = 'Imports exam questions from a JSON file. Links exam_year and source_university from metadata.'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='The path to the JSON file to import')

    def handle(self, *args, **kwargs):
        json_file_path = kwargs['json_file']
        
        if not os.path.exists(json_file_path):
            self.stdout.write(self.style.ERROR(f'File "{json_file_path}" does not exist.'))
            return

        with open(json_file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                self.stdout.write(self.style.ERROR(f'Invalid JSON file: {e}'))
                return

        metadata = data.get('metadata', {})
        questions_data = data.get('questions', [])

        if not questions_data:
            self.stdout.write(self.style.WARNING('No questions found in the JSON file.'))
            return

        uni_code = metadata.get('university_code')
        col_code = metadata.get('college_code')
        sub_code = metadata.get('subject_code')
        exam_year = metadata.get('exam_year')        # سنة الامتحان من الـ metadata
        source_type = metadata.get('source_type')     # past_exam, question_bank, etc.

        try:
            with transaction.atomic():
                # 1. جلب/إنشاء الجامعة
                university, uni_created = University.objects.get_or_create(
                    code=uni_code, 
                    defaults={'name': f'جامعة {uni_code}'}
                )
                if uni_created:
                    self.stdout.write(f'  ✅ Created University: {uni_code}')
                
                # 2. جلب/إنشاء الكلية
                college, col_created = College.objects.get_or_create(
                    code=col_code, 
                    university=university,
                    defaults={'name': f'كلية {col_code}'}
                )
                if col_created:
                    self.stdout.write(f'  ✅ Created College: {col_code}')
                
                # 3. جلب/إنشاء المادة
                subject, sub_created = Subject.objects.get_or_create(
                    code=sub_code,
                    defaults={'name': f'مادة {sub_code}'}
                )
                if sub_created:
                    self.stdout.write(f'  ✅ Created Subject: {sub_code}')
                
                # ربط المادة بالكلية
                college.subjects.add(subject)

                # 4. إنشاء الأسئلة والخيارات
                created_q = 0
                created_o = 0
                
                for q_data in questions_data:
                    question = Question.objects.create(
                        subject=subject,
                        grade_level=q_data.get('grade_level', 12),
                        unit=q_data.get('unit', 1),
                        text=q_data.get('text', ''),
                        explanation=q_data.get('explanation', ''),
                        exam_year=exam_year,                    # ربط سنة الامتحان
                        source_university=university,           # ربط الجامعة المصدر
                        times_appeared=1,                       # أول ظهور
                    )
                    created_q += 1
                    
                    # بناء الخيارات
                    correct_id = q_data.get('correct_identifier')
                    options = []
                    for opt in q_data.get('options', []):
                        identifier = opt.get('identifier')
                        options.append(Option(
                            question=question,
                            identifier=identifier,
                            text=opt.get('text', ''),
                            is_correct=(identifier == correct_id)
                        ))
                    
                    Option.objects.bulk_create(options)
                    created_o += len(options)

            self.stdout.write(self.style.SUCCESS(
                f'\n🎉 Successfully imported!\n'
                f'   University: {uni_code} | College: {col_code} | Subject: {sub_code}\n'
                f'   Year: {exam_year} | Questions: {created_q} | Options: {created_o}'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Import failed. Transaction rolled back.\n   Error: {str(e)}'))
