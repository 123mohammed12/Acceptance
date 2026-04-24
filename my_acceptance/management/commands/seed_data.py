import random
from django.core.management.base import BaseCommand
from django.db import transaction
from my_acceptance.models import University, College, Subject, Question, Option

class Command(BaseCommand):
    help = 'Seeds the database with realistic Yemeni university admission data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('\n[Start] بدء تهيئة قاعدة البيانات ببيانات تجريبية...\n')
        
        try:
            with transaction.atomic():
                # ══════════════════════════════════════════
                # 1. الجامعات
                # ══════════════════════════════════════════
                universities_data = [
                    {'code': 'SU', 'name': 'جامعة صنعاء'},
                    {'code': 'AU', 'name': 'جامعة عدن'},
                    {'code': 'TU', 'name': 'جامعة تعز'},
                    {'code': 'HU', 'name': 'جامعة حضرموت'},
                    {'code': 'IU', 'name': 'جامعة إب'},
                ]
                
                universities = {}
                for u in universities_data:
                    uni, created = University.objects.get_or_create(code=u['code'], defaults={'name': u['name']})
                    universities[u['code']] = uni
                    status = '[Created] أُنشئت' if created else '[Exists] موجودة'
                    self.stdout.write(f'  {status}: {uni.name}')

                # ══════════════════════════════════════════
                # 2. المواد
                # ══════════════════════════════════════════
                subjects_data = [
                    {'code': 'BIO', 'name': 'الأحياء'},
                    {'code': 'CHEM', 'name': 'الكيمياء'},
                    {'code': 'PHY', 'name': 'الفيزياء'},
                    {'code': 'MATH', 'name': 'الرياضيات'},
                    {'code': 'ENG', 'name': 'اللغة الإنجليزية'},
                    {'code': 'ARB', 'name': 'اللغة العربية'},
                    {'code': 'ISL', 'name': 'التربية الإسلامية'},
                ]
                
                subjects = {}
                for s in subjects_data:
                    sub, created = Subject.objects.get_or_create(code=s['code'], defaults={'name': s['name']})
                    subjects[s['code']] = sub
                    status = '[Created]' if created else '[Exists]'
                    self.stdout.write(f'  {status} مادة: {sub.name}')

                # ══════════════════════════════════════════
                # 3. الكليات (مصنفة)
                # ══════════════════════════════════════════
                colleges_data = [
                    # ── الكليات الطبية ──
                    {'code': 'MED', 'name': 'الطب البشري', 'cat': 'medical', 'icon': 'local_hospital',
                     'uni': 'SU', 'subjects': ['BIO', 'CHEM', 'PHY', 'ENG'], 'hw': 30, 'ew': 70},
                    {'code': 'PHARM', 'name': 'الصيدلة', 'cat': 'medical', 'icon': 'medication',
                     'uni': 'SU', 'subjects': ['BIO', 'CHEM', 'PHY'], 'hw': 30, 'ew': 70},
                    {'code': 'DENT', 'name': 'طب الأسنان', 'cat': 'medical', 'icon': 'local_hospital',
                     'uni': 'SU', 'subjects': ['BIO', 'CHEM', 'PHY'], 'hw': 30, 'ew': 70},
                    {'code': 'NURS', 'name': 'التمريض', 'cat': 'medical', 'icon': 'biotech',
                     'uni': 'SU', 'subjects': ['BIO', 'CHEM'], 'hw': 40, 'ew': 60},
                    {'code': 'LAB', 'name': 'المختبرات الطبية', 'cat': 'medical', 'icon': 'biotech',
                     'uni': 'AU', 'subjects': ['BIO', 'CHEM', 'PHY'], 'hw': 35, 'ew': 65},
                    
                    # ── الكليات الهندسية ──
                    {'code': 'CS', 'name': 'هندسة الحاسوب', 'cat': 'engineering', 'icon': 'computer',
                     'uni': 'SU', 'subjects': ['MATH', 'PHY', 'ENG'], 'hw': 30, 'ew': 70},
                    {'code': 'CE', 'name': 'الهندسة المدنية', 'cat': 'engineering', 'icon': 'architecture',
                     'uni': 'SU', 'subjects': ['MATH', 'PHY'], 'hw': 30, 'ew': 70},
                    {'code': 'EE', 'name': 'الهندسة الكهربائية', 'cat': 'engineering', 'icon': 'electric_bolt',
                     'uni': 'AU', 'subjects': ['MATH', 'PHY'], 'hw': 30, 'ew': 70},
                    
                    # ── الكليات العلمية ──
                    {'code': 'SCI_BIO', 'name': 'العلوم (أحياء)', 'cat': 'science', 'icon': 'science',
                     'uni': 'TU', 'subjects': ['BIO', 'CHEM'], 'hw': 40, 'ew': 60},
                    {'code': 'SCI_MATH', 'name': 'العلوم (رياضيات)', 'cat': 'science', 'icon': 'science',
                     'uni': 'TU', 'subjects': ['MATH', 'PHY'], 'hw': 40, 'ew': 60},
                    
                    # ── الكليات الإنسانية ──
                    {'code': 'LAW', 'name': 'الشريعة والقانون', 'cat': 'humanities', 'icon': 'school',
                     'uni': 'SU', 'subjects': ['ARB', 'ISL'], 'hw': 50, 'ew': 50},
                    {'code': 'ARTS', 'name': 'الآداب', 'cat': 'humanities', 'icon': 'school',
                     'uni': 'IU', 'subjects': ['ARB', 'ENG'], 'hw': 50, 'ew': 50},
                ]
                
                colleges = {}
                for c in colleges_data:
                    college, created = College.objects.get_or_create(
                        code=c['code'], university=universities[c['uni']],
                        defaults={
                            'name': c['name'], 'category': c['cat'], 'icon_name': c['icon'],
                            'high_school_weight': c['hw'], 'exam_weight': c['ew'],
                        }
                    )
                    for sc in c['subjects']:
                        college.subjects.add(subjects[sc])
                    colleges[c['code']] = college
                    status = '[Created]' if created else '[Exists]'
                    self.stdout.write(f'  {status} كلية: {college.name} ({college.get_category_display()})')

                # ══════════════════════════════════════════
                # 4. الأسئلة التجريبية
                # ══════════════════════════════════════════
                self.stdout.write('\n[Write] إنشاء أسئلة تجريبية...')
                
                q_count = 0
                
                # ── أسئلة الأحياء ──
                bio_questions = [
                    {'gl': 12, 'u': 1, 'text': 'ما هي العملية الانقسامية التي تؤدي إلى إنتاج أمشاج أحادية المجموعة الكروموسومية (1n)؟',
                     'opts': [('A', 'الاندماج الخلوي'), ('B', 'الانقسام المنصف (الاختزالي)'), ('C', 'الانقسام المتساوي'), ('D', 'العبور الجيني')],
                     'correct': 'B', 'exp': 'الانقسام الاختزالي يقوم بتنصيف عدد الكروموسومات للحفاظ على ثبات العدد الكروموسومي.'},
                    {'gl': 12, 'u': 2, 'text': 'أي من الخلايا التالية مسؤولة عن المناعة الخلوية في جسم الإنسان؟',
                     'opts': [('A', 'خلايا الدم الحمراء'), ('B', 'الخلايا البائية'), ('C', 'الصفائح الدموية'), ('D', 'الخلايا التائية')],
                     'correct': 'D', 'exp': 'الخلايا التائية تلعب دوراً رئيسياً في المناعة الخلوية بمهاجمة الخلايا المصابة مباشرة.'},
                    {'gl': 11, 'u': 1, 'text': 'ما هي الوحدة البنائية الأساسية للبروتينات؟',
                     'opts': [('A', 'الأحماض الدهنية'), ('B', 'الأحماض الأمينية'), ('C', 'السكريات الأحادية'), ('D', 'النيوكليوتيدات')],
                     'correct': 'B', 'exp': 'الأحماض الأمينية هي اللبنات الأساسية للبروتينات ترتبط بروابط ببتيدية.'},
                    {'gl': 10, 'u': 3, 'text': 'ما العضية الخلوية المعروفة بـ "مصنع الطاقة" لإنتاج ATP؟',
                     'opts': [('A', 'أجسام جولجي'), ('B', 'الشبكة الإندوبلازمية'), ('C', 'الميتوكوندريا'), ('D', 'البلاستيدات الخضراء')],
                     'correct': 'C', 'exp': 'الميتوكوندريا متخصصة بالتنفس الخلوي لإنتاج الطاقة على شكل ATP.'},
                    {'gl': 12, 'u': 4, 'text': 'القاعدة النيتروجينية الموجودة في RNA ولا توجد في DNA هي:',
                     'opts': [('A', 'الأدينين'), ('B', 'الجوانين'), ('C', 'اليوراسيل'), ('D', 'الثايمين')],
                     'correct': 'C', 'exp': 'في RNA يتم استبدال الثايمين باليوراسيل.'},
                    {'gl': 11, 'u': 2, 'text': 'ما الإنزيم الموجود في اللعاب الذي يبدأ هضم الكربوهيدرات؟',
                     'opts': [('A', 'الببسين'), ('B', 'الأميليز اللعابي'), ('C', 'الليباز'), ('D', 'التربسين')],
                     'correct': 'B', 'exp': 'الأميليز يُفرز من الغدد اللعابية ويفكك النشا إلى سكريات أبسط.'},
                    {'gl': 12, 'u': 5, 'text': 'أي أجزاء الدماغ يتحكم في توازن الجسم وتنسيق الحركات؟',
                     'opts': [('A', 'المخ'), ('B', 'المخيخ'), ('C', 'النخاع المستطيل'), ('D', 'تحت المهاد')],
                     'correct': 'B', 'exp': 'المخيخ مسؤول عن حفظ توازن الجسم وتنسيق الحركات العضلية.'},
                    {'gl': 11, 'u': 6, 'text': 'الهرمون الذي يُفرز من البنكرياس ويخفض مستوى الجلوكوز في الدم هو:',
                     'opts': [('A', 'الجلوكاجون'), ('B', 'الكورتيزول'), ('C', 'الأدرينالين'), ('D', 'الأنسولين')],
                     'correct': 'D', 'exp': 'الأنسولين يُفرز من خلايا بيتا في جزر لانجرهانز بالبنكرياس.'},
                    {'gl': 10, 'u': 4, 'text': 'فصيلة الدم "المعطي العام" التي لا تحتوي مولدات ضد (A و B) هي:',
                     'opts': [('A', 'AB'), ('B', 'A'), ('C', 'O'), ('D', 'B')],
                     'correct': 'C', 'exp': 'فصيلة O خالية من الأنتيجينات فلا يهاجمها جهاز المناعة عند النقل.'},
                    {'gl': 10, 'u': 1, 'text': 'ما الجدار الخارجي الصلب الذي يحمي الخلية النباتية؟',
                     'opts': [('A', 'السيتوبلازم'), ('B', 'الغشاء البلازمي'), ('C', 'الجدار الخلوي السليلوزي'), ('D', 'الشبكة الإندوبلازمية')],
                     'correct': 'C', 'exp': 'الجدار الخلوي السليلوزي يميز الخلية النباتية ويوفر الصلابة.'},
                ]
                
                for q in bio_questions:
                    for year in [2022, 2023, 2024]:
                        for uni_code in ['SU', 'AU']:
                            question = Question.objects.create(
                                subject=subjects['BIO'], grade_level=q['gl'], unit=q['u'],
                                text=q['text'], explanation=q['exp'],
                                exam_year=year, source_university=universities[uni_code],
                                times_appeared=random.randint(1, 5),
                            )
                            opts = []
                            for oid, otext in q['opts']:
                                opts.append(Option(question=question, identifier=oid, text=otext, is_correct=(oid == q['correct'])))
                            Option.objects.bulk_create(opts)
                            q_count += 1

                # ── أسئلة الكيمياء (مع LaTeX) ──
                chem_questions = [
                    {'gl': 12, 'u': 1, 'text': 'ما الصيغة الكيميائية لحمض الكبريتيك؟',
                     'opts': [('A', '$HCl$'), ('B', '$H_2SO_4$'), ('C', '$HNO_3$'), ('D', '$H_3PO_4$')],
                     'correct': 'B', 'exp': 'حمض الكبريتيك $H_2SO_4$ من أقوى الأحماض المعدنية ويستخدم في الصناعة.'},
                    {'gl': 12, 'u': 2, 'text': 'عند تفاعل الصوديوم مع الماء ينتج:',
                     'opts': [('A', '$NaCl + H_2$'), ('B', '$NaOH + H_2$'), ('C', '$Na_2O + H_2$'), ('D', '$NaOH + O_2$')],
                     'correct': 'B', 'exp': 'التفاعل: $2Na + 2H_2O → 2NaOH + H_2↑$ وهو تفاعل طارد للحرارة.'},
                    {'gl': 11, 'u': 3, 'text': 'الرابطة التي تتكون بين ذرات الكربون في الألماس هي:',
                     'opts': [('A', 'رابطة أيونية'), ('B', 'رابطة تساهمية أحادية'), ('C', 'رابطة تساهمية رباعية'), ('D', 'رابطة فلزية')],
                     'correct': 'C', 'exp': 'كل ذرة كربون في الألماس ترتبط بأربع ذرات كربون أخرى بروابط تساهمية.'},
                    {'gl': 11, 'u': 1, 'text': 'العدد الذري لعنصر الكربون $C$ يساوي:',
                     'opts': [('A', '8'), ('B', '12'), ('C', '6'), ('D', '14')],
                     'correct': 'C', 'exp': 'العدد الذري للكربون = 6 أي يحتوي على 6 بروتونات في نواته.'},
                    {'gl': 10, 'u': 2, 'text': 'ما هو الغاز الناتج عن تفاعل حمض مع كربونات الكالسيوم $CaCO_3$؟',
                     'opts': [('A', '$O_2$'), ('B', '$H_2$'), ('C', '$CO_2$'), ('D', '$N_2$')],
                     'correct': 'C', 'exp': 'التفاعل ينتج غاز ثاني أكسيد الكربون $CO_2$ الذي يُعكر ماء الجير.'},
                    {'gl': 12, 'u': 3, 'text': 'عدد مولات $NaCl$ في 58.5 جرام يساوي:',
                     'opts': [('A', '0.5 مول'), ('B', '1 مول'), ('C', '2 مول'), ('D', '1.5 مول')],
                     'correct': 'B', 'exp': 'الكتلة المولية لـ $NaCl$ = 23 + 35.5 = 58.5 جم/مول، إذن 58.5/58.5 = 1 مول.'},
                    {'gl': 11, 'u': 4, 'text': 'المحلول الذي قيمة $pH$ له تساوي 3 يكون:',
                     'opts': [('A', 'متعادلاً'), ('B', 'حمضياً'), ('C', 'قاعدياً'), ('D', 'ملحياً')],
                     'correct': 'B', 'exp': 'قيم $pH$ أقل من 7 تدل على محاليل حمضية.'},
                    {'gl': 10, 'u': 5, 'text': 'ما هو العنصر الأكثر وفرة في القشرة الأرضية؟',
                     'opts': [('A', 'الحديد $Fe$'), ('B', 'الألمنيوم $Al$'), ('C', 'الأكسجين $O$'), ('D', 'السيليكون $Si$')],
                     'correct': 'C', 'exp': 'الأكسجين يشكل حوالي 46% من كتلة القشرة الأرضية.'},
                ]
                
                for q in chem_questions:
                    for year in [2022, 2023, 2024]:
                        question = Question.objects.create(
                            subject=subjects['CHEM'], grade_level=q['gl'], unit=q['u'],
                            text=q['text'], explanation=q['exp'],
                            exam_year=year, source_university=universities['SU'],
                            times_appeared=random.randint(1, 4),
                        )
                        opts = []
                        for oid, otext in q['opts']:
                            opts.append(Option(question=question, identifier=oid, text=otext, is_correct=(oid == q['correct'])))
                        Option.objects.bulk_create(opts)
                        q_count += 1

                # ── أسئلة الفيزياء ──
                phy_questions = [
                    {'gl': 12, 'u': 1, 'text': 'وحدة قياس القوة في النظام الدولي هي:',
                     'opts': [('A', 'الجول'), ('B', 'النيوتن'), ('C', 'الباسكال'), ('D', 'الواط')],
                     'correct': 'B', 'exp': 'النيوتن N هو وحدة القوة = كغ × م/ث².'},
                    {'gl': 11, 'u': 2, 'text': 'إذا تضاعفت المسافة بين شحنتين كهربائيتين فإن القوة بينهما:',
                     'opts': [('A', 'تتضاعف'), ('B', 'تنخفض للنصف'), ('C', 'تنخفض للربع'), ('D', 'لا تتغير')],
                     'correct': 'C', 'exp': 'حسب قانون كولوم: القوة تتناسب عكسياً مع مربع المسافة $F \\propto 1/r^2$.'},
                    {'gl': 12, 'u': 3, 'text': 'سرعة الصوت تكون أكبر في:',
                     'opts': [('A', 'الفراغ'), ('B', 'الهواء'), ('C', 'الماء'), ('D', 'الفولاذ')],
                     'correct': 'D', 'exp': 'سرعة الصوت تزداد في الأوساط الأكثر كثافة وصلابة (صلب > سائل > غاز).'},
                    {'gl': 10, 'u': 1, 'text': 'أي مما يلي يُعتبر كمية متجهة؟',
                     'opts': [('A', 'الكتلة'), ('B', 'درجة الحرارة'), ('C', 'السرعة'), ('D', 'الزمن')],
                     'correct': 'C', 'exp': 'السرعة (Velocity) كمية متجهة لأن لها مقدار واتجاه، بعكس السرعة القياسية (Speed).'},
                    {'gl': 12, 'u': 4, 'text': 'تنص نظرية النسبية الخاصة على أن سرعة الضوء في الفراغ:',
                     'opts': [('A', 'تتغير حسب المراقب'), ('B', 'ثابتة لجميع المراقبين'), ('C', 'تتأثر بالجاذبية'), ('D', 'تساوي صفراً')],
                     'correct': 'B', 'exp': 'سرعة الضوء في الفراغ ثابتة = $3 \\times 10^8$ م/ث لجميع المراقبين.'},
                    {'gl': 11, 'u': 5, 'text': 'قانون نيوتن الثاني ينص على أن: $F = m \\times a$. إذا كانت الكتلة 5 كغ والتسارع 2 م/ث² فإن القوة تساوي:',
                     'opts': [('A', '2.5 نيوتن'), ('B', '7 نيوتن'), ('C', '10 نيوتن'), ('D', '3 نيوتن')],
                     'correct': 'C', 'exp': '$F = 5 \\times 2 = 10$ نيوتن.'},
                ]
                
                for q in phy_questions:
                    for year in [2022, 2023, 2024]:
                        question = Question.objects.create(
                            subject=subjects['PHY'], grade_level=q['gl'], unit=q['u'],
                            text=q['text'], explanation=q['exp'],
                            exam_year=year, source_university=universities['TU'],
                            times_appeared=random.randint(1, 3),
                        )
                        opts = []
                        for oid, otext in q['opts']:
                            opts.append(Option(question=question, identifier=oid, text=otext, is_correct=(oid == q['correct'])))
                        Option.objects.bulk_create(opts)
                        q_count += 1

                # ── أسئلة الرياضيات (مع LaTeX) ──
                math_questions = [
                    {'gl': 12, 'u': 1, 'text': 'ما قيمة $\\lim_{x \\to 0} \\frac{\\sin(x)}{x}$؟',
                     'opts': [('A', '0'), ('B', '1'), ('C', '$\\infty$'), ('D', 'غير معرّف')],
                     'correct': 'B', 'exp': 'هذه من النهايات الأساسية في التفاضل وقيمتها تساوي 1.'},
                    {'gl': 12, 'u': 2, 'text': 'مشتقة الدالة $f(x) = x^3 + 2x$ هي:',
                     'opts': [('A', '$3x^2$'), ('B', '$3x^2 + 2$'), ('C', '$x^2 + 2$'), ('D', '$3x + 2$')],
                     'correct': 'B', 'exp': '$f\'(x) = 3x^2 + 2$ بتطبيق قاعدة القوى: مشتقة $x^n = nx^{n-1}$.'},
                    {'gl': 11, 'u': 3, 'text': 'حل المعادلة $2x + 6 = 0$ هو:',
                     'opts': [('A', '$x = 3$'), ('B', '$x = -3$'), ('C', '$x = 6$'), ('D', '$x = -6$')],
                     'correct': 'B', 'exp': '$2x = -6$، إذن $x = -3$.'},
                    {'gl': 10, 'u': 1, 'text': 'مساحة المثلث الذي قاعدته 8 سم وارتفاعه 5 سم تساوي:',
                     'opts': [('A', '40 سم²'), ('B', '20 سم²'), ('C', '13 سم²'), ('D', '80 سم²')],
                     'correct': 'B', 'exp': 'مساحة المثلث = $\\frac{1}{2} \\times 8 \\times 5 = 20$ سم².'},
                    {'gl': 12, 'u': 4, 'text': 'قيمة $\\int_0^2 x^2 \\, dx$ تساوي:',
                     'opts': [('A', '$\\frac{2}{3}$'), ('B', '$\\frac{4}{3}$'), ('C', '$\\frac{8}{3}$'), ('D', '4')],
                     'correct': 'C', 'exp': '$\\int_0^2 x^2 dx = [\\frac{x^3}{3}]_0^2 = \\frac{8}{3} - 0 = \\frac{8}{3}$.'},
                ]
                
                for q in math_questions:
                    for year in [2022, 2023]:
                        question = Question.objects.create(
                            subject=subjects['MATH'], grade_level=q['gl'], unit=q['u'],
                            text=q['text'], explanation=q['exp'],
                            exam_year=year, source_university=universities['SU'],
                            times_appeared=random.randint(1, 4),
                        )
                        opts = []
                        for oid, otext in q['opts']:
                            opts.append(Option(question=question, identifier=oid, text=otext, is_correct=(oid == q['correct'])))
                        Option.objects.bulk_create(opts)
                        q_count += 1

            self.stdout.write(self.style.SUCCESS(
                f'\n[Success] تمت التهيئة بنجاح!\n'
                f'   [+] {University.objects.count()} جامعات\n'
                f'   [+] {Subject.objects.count()} مواد\n'
                f'   [+] {College.objects.count()} كليات\n'
                f'   [+] {Question.objects.count()} سؤال\n'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[Error] فشلت التهيئة: {str(e)}'))
