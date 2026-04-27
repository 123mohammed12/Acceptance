from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import hashlib, secrets

class University(models.Model):
    name = models.CharField(max_length=255, verbose_name='اسم الجامعة')
    code = models.CharField(max_length=50, unique=True, verbose_name='رمز الجامعة')
    logo = models.ImageField(upload_to='universities/', null=True, blank=True, verbose_name='شعار الجامعة')
    description = models.TextField(blank=True, verbose_name='الوصف')
    is_active = models.BooleanField(default=True, verbose_name='مفعل')

    class Meta:
        verbose_name = 'الجامعة'
        verbose_name_plural = 'الجامعات'

    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=100, verbose_name='اسم المادة')
    code = models.CharField(max_length=50, unique=True, verbose_name='رمز المادة')
    is_active = models.BooleanField(default=True, verbose_name='مفعل')
    
    class Meta:
        verbose_name = 'المادة'
        verbose_name_plural = 'المواد'

    def __str__(self):
        return self.name

class College(models.Model):
    COLLEGE_CATEGORIES = [
        ('medical', 'الكليات الطبية'),
        ('engineering', 'الكليات الهندسية'),
        ('science', 'الكليات العلمية'),
        ('humanities', 'الكليات الإنسانية'),
    ]
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='colleges', verbose_name='الجامعة')
    name = models.CharField(max_length=255, verbose_name='اسم الكلية/التخصص')
    code = models.CharField(max_length=50, verbose_name='رمز الكلية')
    category = models.CharField(max_length=20, choices=COLLEGE_CATEGORIES, default='science', verbose_name='التصنيف')
    icon_name = models.CharField(max_length=50, default='school', help_text='اسم أيقونة Flutter مثل: local_hospital, computer, science', verbose_name='الأيقونة')
    subjects = models.ManyToManyField(Subject, related_name='required_for_colleges', verbose_name='مقررات القبول')
    high_school_weight = models.DecimalField(max_digits=5, decimal_places=2, default=30.00, verbose_name='نسبة معدل الثانوية (%)')
    exam_weight = models.DecimalField(max_digits=5, decimal_places=2, default=70.00, verbose_name='نسبة اختبار القبول (%)')
    is_active = models.BooleanField(default=True, verbose_name='مفعل')

    class Meta:
        verbose_name = 'الكلية'
        verbose_name_plural = 'الكليات'

    def __str__(self):
        return f"{self.name} - {self.university.name}"

class Question(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='questions', verbose_name='المادة')
    grade_level = models.IntegerField(help_text="الصف الدراسي مثلا 10، 11، 12", verbose_name='الصف الدراسي')
    unit = models.IntegerField(help_text="رقم الوحدة في الكتاب", verbose_name='الوحدة')
    text = models.TextField(verbose_name='نص السؤال')
    explanation = models.TextField(null=True, blank=True, help_text="شرح الإجابة الصحيحة", verbose_name='الشرح')
    image = models.ImageField(upload_to='questions_images/', null=True, blank=True, verbose_name='صورة السؤال')
    exam_year = models.IntegerField(null=True, blank=True, help_text='سنة الامتحان الأصلي الذي جاء منه السؤال', verbose_name='سنة الامتحان')
    source_university = models.ForeignKey('University', null=True, blank=True, on_delete=models.SET_NULL, related_name='sourced_questions', verbose_name='الجامعة المصدر')
    source_college = models.ForeignKey('College', null=True, blank=True, on_delete=models.SET_NULL, related_name='sourced_questions', verbose_name='الكلية المصدر')
    times_appeared = models.IntegerField(default=0, verbose_name='مرات الظهور في امتحانات سابقة') 

    class Meta:
        verbose_name = 'سؤال القبول'
        verbose_name_plural = 'أسئلة القبول'

    def __str__(self):
        return str(self.text)[:50]

class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    identifier = models.CharField(max_length=1, verbose_name='الحرف (A/B/C/D)') # A, B, C, D
    text = models.CharField(max_length=500, verbose_name='النص')
    is_correct = models.BooleanField(default=False, verbose_name='إجابة صحيحة')

    class Meta:
        verbose_name = 'خيار الإجابة'
        verbose_name_plural = 'خيارات الإجابات'

    def __str__(self):
        return f"{self.identifier}: {self.text}"

class PDFResource(models.Model):
    RESOURCE_TYPES = [
        ('past_exam', 'نموذج اختبار سابق'),
        ('question_bank', 'بنك أسئلة مرجعي'),
    ]
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='pdf_resources', verbose_name='الكلية')
    subject = models.ForeignKey(Subject, null=True, blank=True, on_delete=models.SET_NULL, related_name='pdf_resources', verbose_name='المادة')
    title = models.CharField(max_length=255, verbose_name='العنوان')
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES, verbose_name='نوع الملف')
    year = models.IntegerField(null=True, blank=True, verbose_name='سنة الاختبار')
    file = models.FileField(upload_to='pdf_resources/', verbose_name='ملف PDF')

    class Meta:
        verbose_name = 'المرجع الرقمي (PDF)'
        verbose_name_plural = 'المراجع الرقمية (PDF)'

    def __str__(self):
        return self.title

# --------------------------------------------------------
# جداول تتبع نتائج الطلاب والمراجعة
# --------------------------------------------------------

class TestSession(models.Model):
    TEST_TYPES = [
        ('unit', 'اختبار وحدة'),
        ('book', 'اختبار كتاب'),
        ('mock', 'اختبار قبول شامل'),
        ('year_sim', 'محاكاة سنة'),
        ('most_repeated', 'الأكثر تكراراً'),
        ('bank', 'بنك أسئلة مخصص'),
        ('subject_all', 'مادة شاملة'),
        ('favorites', 'اختبار من المفضلة'),
    ]
    EXAM_MODES = [
        ('instant', 'الوضع التدريبي (فوري)'),
        ('review', 'وضع الامتحان الحقيقي'),
    ]
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_sessions', verbose_name='الطالب')
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='الكلية')
    test_type = models.CharField(max_length=20, choices=TEST_TYPES, verbose_name='نوع الاختبار')
    total_questions = models.IntegerField(verbose_name='عدد الأسئلة الإجمالي')
    correct_answers_count = models.IntegerField(default=0, verbose_name='الإجابات الصحيحة')
    score_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name='النسبة المئوية')
    exam_mode = models.CharField(max_length=10, choices=EXAM_MODES, default='instant', verbose_name='وضع الاختبار')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ المحاولة')

    class Meta:
        verbose_name = 'جلسة اختبار'
        verbose_name_plural = 'جلسات الاختبار'

    def __str__(self):
        return f"{self.student.username} - {self.get_test_type_display()} - {self.score_percentage}%"

class StudentAnswer(models.Model):
    session = models.ForeignKey(TestSession, on_delete=models.CASCADE, related_name='student_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE, null=True, blank=True)
    is_correct = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'إجابة الطالب'
        verbose_name_plural = 'إجابات الطلاب'

    def __str__(self):
        return f"Q: {self.question.id} | Correct: {self.is_correct}"

# --------------------------------------------------------
# نظام إدارة اشتراك وأمان الطالب (Security & Freemium)
# --------------------------------------------------------

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='المستخدم')
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name='رقم الهاتف')
    device_id = models.CharField(max_length=255, null=True, blank=True, help_text="بصمة الجهاز لمنع مشاركة الحساب", verbose_name='معرف الجهاز النشط')
    is_premium = models.BooleanField(default=False, help_text="تفعيل الاشتراك الشامل للطالب", verbose_name='حساب مدفوع (Premium)')
    free_past_exam_trials = models.IntegerField(default=0, help_text="عدد اختبارات القبول التفاعلية المجانية المستخدمة (الحد: 2)", verbose_name='محاولات اختبارات القبول المجانية')
    free_challenge_trials = models.IntegerField(default=0, help_text="عدد التحديات المجانية المستخدمة (الحد: 2)", verbose_name='محاولات التحديات المجانية')
    target_college = models.ForeignKey('College', null=True, blank=True, on_delete=models.SET_NULL, related_name='targeting_students', verbose_name='الكلية المستهدفة', help_text='كلية أحلام الطالب للتوصيات المخصصة')

    class Meta:
        verbose_name = 'ملف الطالب (الاشتراك)'
        verbose_name_plural = 'ملفات الطلاب (الاشتراكات)'

    def __str__(self):
        status = "مدفوع" if self.is_premium else "مجاني"
        return f"{self.user.username} - {self.phone_number} ({status})"


class FavoriteQuestion(models.Model):
    """نموذج المفضلة — يخزن الأسئلة التي حفظها الطالب لمراجعتها لاحقاً"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_questions', verbose_name='الطالب')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='favorited_by', verbose_name='السؤال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإضافة')

    class Meta:
        verbose_name = 'سؤال مفضل'
        verbose_name_plural = 'الأسئلة المفضلة'
        unique_together = ('user', 'question')  # منع التكرار

    def __str__(self):
        return f"{self.user.username} ❤️ Q#{self.question.id}"


class ActivationCode(models.Model):
    """كود تفعيل الاشتراك — يُستخدم مرة واحدة فقط بعد التحقق من الدفع"""
    code_hash = models.CharField(max_length=64, unique=True, verbose_name='بصمة الكود (SHA-256)',
                                  help_text="يُخزَّن مُشفّراً ولا يمكن معرفة الكود الأصلي")
    code_display = models.CharField(max_length=16, blank=True, verbose_name='الكود (يظهر مرة واحدة عند الإنشاء)',
                                     help_text="يُعرض فقط عند الإنشاء ثم يُمسح تلقائياً للأمان")
    is_used = models.BooleanField(default=False, verbose_name='مُستخدَم')
    used_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='used_codes', verbose_name='استُخدم بواسطة')
    used_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الاستخدام')
    duration_days = models.IntegerField(default=365, verbose_name='مدة الاشتراك (أيام)',
                                         help_text="عدد أيام الاشتراك التي يمنحها هذا الكود")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    created_by_admin = models.CharField(max_length=100, blank=True, verbose_name='أنشأه المسؤول')
    note = models.CharField(max_length=255, blank=True, verbose_name='ملاحظة',
                             help_text="مثال: اسم الطالب أو رقم الحوالة")

    class Meta:
        verbose_name = 'كود تفعيل'
        verbose_name_plural = 'أكواد التفعيل'
        ordering = ['-created_at']

    def __str__(self):
        status = "✅ مُستخدم" if self.is_used else "⏳ متاح"
        return f"كود #{self.id} — {status}"

    @staticmethod
    def hash_code(plain_code):
        """تشفير الكود بـ SHA-256"""
        return hashlib.sha256(plain_code.strip().upper().encode()).hexdigest()

    @classmethod
    def generate(cls, duration_days=365, admin_name='', note=''):
        """توليد كود عشوائي آمن — يُعاد الكود الأصلي مرة واحدة فقط"""
        plain = secrets.token_hex(4).upper()  # 8 حروف عشوائية آمنة
        code_hash = cls.hash_code(plain)
        obj = cls.objects.create(
            code_hash=code_hash,
            code_display=plain,  # يظهر مؤقتاً للأدمن
            duration_days=duration_days,
            created_by_admin=admin_name,
            note=note,
        )
        return obj, plain

    def activate_for_user(self, user):
        """تفعيل الكود لمستخدم — مرة واحدة فقط"""
        if self.is_used:
            raise ValueError("هذا الكود مُستخدم بالفعل.")
        self.is_used = True
        self.used_by = user
        self.used_at = timezone.now()
        self.code_display = ''  # مسح الكود من القاعدة للأمان
        self.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.is_premium = True
        profile.save()

# --------------------------------------------------------
# نظام رفع الأسئلة من ملفات JSON
# --------------------------------------------------------

class ExamDataJSONUpload(models.Model):
    file = models.FileField(upload_to='exam_uploads/', verbose_name='ملف الأسئلة (JSON)')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الرفع')
    processed = models.BooleanField(default=False, verbose_name='تمت المعالجة')
    log = models.TextField(blank=True, verbose_name='سجل المعالجة')

    class Meta:
        verbose_name = 'رفع بيانات اختبار (JSON)'
        verbose_name_plural = 'رفع بيانات الاختبارات (JSON)'

    def __str__(self):
        return f"ملف مرفوع في {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"


# --------------------------------------------------------
# نظام البطاقات التعليمية (Spaced Repetition - SM2)
# --------------------------------------------------------

class Deck(models.Model):
    """مجموعة بطاقات تعليمية مرتبطة بمادة معينة"""
    name = models.CharField(max_length=255, verbose_name='اسم المجموعة')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='decks', verbose_name='المادة')
    description = models.TextField(blank=True, verbose_name='الوصف')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')

    class Meta:
        verbose_name = 'مجموعة بطاقات'
        verbose_name_plural = 'مجموعات البطاقات'
        unique_together = ('name', 'subject')

    def __str__(self):
        return f"{self.name} — {self.subject.name}"


class Flashcard(models.Model):
    """بطاقة تعليمية واحدة: وجه أمامي (سؤال) ووجه خلفي (إجابة)"""
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name='cards', verbose_name='المجموعة')
    front = models.TextField(verbose_name='الوجه الأمامي (السؤال)')
    back = models.TextField(verbose_name='الوجه الخلفي (الإجابة)')
    order = models.IntegerField(default=0, verbose_name='الترتيب')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإضافة')

    class Meta:
        verbose_name = 'بطاقة تعليمية'
        verbose_name_plural = 'البطاقات التعليمية'
        ordering = ['order', 'id']

    def __str__(self):
        return f"بطاقة #{self.id} — {self.front[:40]}"


class UserFlashcardProgress(models.Model):
    """تتبع تقدم المستخدم في مراجعة البطاقات وفق خوارزمية SM-2"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flashcard_progress', verbose_name='الطالب')
    flashcard = models.ForeignKey(Flashcard, on_delete=models.CASCADE, related_name='user_progress', verbose_name='البطاقة')
    repetitions = models.IntegerField(default=0, verbose_name='عدد التكرارات الناجحة')
    ease_factor = models.FloatField(default=2.5, verbose_name='معامل السهولة')
    interval = models.IntegerField(default=0, verbose_name='الفاصل الزمني (أيام)')
    next_review_date = models.DateField(default=timezone.now, verbose_name='تاريخ المراجعة القادمة')
    last_reviewed = models.DateTimeField(null=True, blank=True, verbose_name='آخر مراجعة')

    class Meta:
        verbose_name = 'تقدم مراجعة بطاقة'
        verbose_name_plural = 'تقدم مراجعة البطاقات'
        unique_together = ('user', 'flashcard')

    def __str__(self):
        return f"{self.user.username} — بطاقة #{self.flashcard.id} — بعد {self.interval} يوم"

    def apply_sm2(self, quality):
        """
        تطبيق خوارزمية SM-2
        quality: 0-5 حيث:
          - 2 = صعب (Hard)
          - 3 = جيد (Good) 
          - 5 = سهل (Easy)
        """
        if quality < 3:
            # الإجابة صعبة: المراجعة في نفس اليوم
            self.repetitions = 0
            self.interval = 0
        else:
            if self.repetitions == 0:
                self.interval = 1
            elif self.repetitions == 1:
                self.interval = 6
            else:
                self.interval = round(self.interval * self.ease_factor)
            self.repetitions += 1

        # تحديث معامل السهولة
        self.ease_factor = max(1.3, self.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))

        # تحديد تاريخ المراجعة القادمة
        self.next_review_date = timezone.now().date() + timezone.timedelta(days=self.interval)
        self.last_reviewed = timezone.now()
        self.save()

    def simulate_sm2(self, quality):
        """
        محاكاة الخوارزمية لمعرفة الفاصل الزمني القادم دون الحفظ.
        يستخدم لعرض الأوقات المتوقعة على الأزرار للمستخدم.
        """
        sim_interval = self.interval
        sim_repetitions = self.repetitions
        sim_ease_factor = self.ease_factor

        if quality < 3:
            sim_interval = 0  # 0 يعني المراجعة في نفس اليوم (بعد دقائق)
        else:
            if sim_repetitions == 0:
                sim_interval = 1
            elif sim_repetitions == 1:
                sim_interval = 6
            else:
                sim_interval = round(sim_interval * sim_ease_factor)

        # تحويل القيمة إلى نص مقروء
        if sim_interval == 0:
            return "10m"
        elif sim_interval == 1:
            return "1d"
        elif sim_interval < 30:
            return f"{sim_interval}d"
        elif sim_interval < 365:
            return f"{sim_interval // 30}mo"
        else:
            return f"{sim_interval // 365}y"


class FlashcardDocxUpload(models.Model):
    """رفع ملف Word يحتوي على بطاقات تعليمية"""
    file = models.FileField(upload_to='flashcard_uploads/', verbose_name='ملف Word (.docx)')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name='المادة')
    deck_name = models.CharField(max_length=255, verbose_name='اسم المجموعة')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الرفع')
    processed = models.BooleanField(default=False, verbose_name='تمت المعالجة')
    log = models.TextField(blank=True, verbose_name='سجل المعالجة')

    class Meta:
        verbose_name = 'رفع بطاقات من ملف Word'
        verbose_name_plural = 'رفع بطاقات من ملفات Word'

    def __str__(self):
        return f"{self.deck_name} — {self.subject.name} ({self.uploaded_at.strftime('%Y-%m-%d')})"

# --------------------------------------------------------
# نظام الإشعارات (Notifications)
# --------------------------------------------------------

class AppNotification(models.Model):
    """إشعارات عامة لجميع المستخدمين (مثال: تم إضافة كذا، تحديث جديد)"""
    title = models.CharField(max_length=255, verbose_name='عنوان الإشعار')
    body = models.TextField(verbose_name='محتوى الإشعار')
    icon_name = models.CharField(max_length=50, blank=True, verbose_name='اسم الأيقونة',
                                  help_text="مثال: science, computer, notification")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ النشر')
    is_active = models.BooleanField(default=True, verbose_name='نشط (يظهر للمستخدمين)')

    class Meta:
        verbose_name = 'إشعار'
        verbose_name_plural = 'الإشعارات والإعلانات'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.created_at.strftime('%Y-%m-%d')})"


# --------------------------------------------------------
# دليل المراجعة للمواضيع المتكررة (Study Guide per Subject/College)
# --------------------------------------------------------

class CollegeStudyGuide(models.Model):
    """دليل مراجعة يحتوي على المواضيع المتكررة والتوصيات لمادة معينة في كلية محددة"""
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='study_guides', verbose_name='الكلية')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='study_guides', verbose_name='المادة')
    title = models.CharField(max_length=255, verbose_name='عنوان الدليل', help_text='مثال: دليل مراجعة الكيمياء — طب بشري')
    content = models.TextField(verbose_name='المحتوى', help_text='المحتوى المُستخرج من ملف الوورد')
    is_active = models.BooleanField(default=True, verbose_name='مفعل')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')

    class Meta:
        verbose_name = 'دليل مراجعة'
        verbose_name_plural = 'أدلة المراجعة'
        unique_together = ('college', 'subject')

    def __str__(self):
        return f"{self.title} — {self.college.name}"


class CollegeStudyGuideUpload(models.Model):
    """رفع ملف Word يحتوي على دليل مراجعة لمادة في كلية"""
    file = models.FileField(upload_to='study_guide_uploads/', verbose_name='ملف Word (.docx)')
    college = models.ForeignKey(College, on_delete=models.CASCADE, verbose_name='الكلية')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name='المادة')
    guide_title = models.CharField(max_length=255, verbose_name='عنوان الدليل')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الرفع')
    processed = models.BooleanField(default=False, verbose_name='تمت المعالجة')
    log = models.TextField(blank=True, verbose_name='سجل المعالجة')

    class Meta:
        verbose_name = 'رفع دليل مراجعة من ملف Word'
        verbose_name_plural = 'رفع أدلة المراجعة من ملفات Word'

    def __str__(self):
        return f"{self.guide_title} — {self.subject.name} ({self.uploaded_at.strftime('%Y-%m-%d')})"

