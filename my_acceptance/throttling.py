from rest_framework.throttling import UserRateThrottle

class ExamGenerationThrottle(UserRateThrottle):
    """
    Custom throttle to limit how many exams a user can generate per minute.
    This prevents scraping bots from generating exams rapidly.
    """
    rate = '30/minute' # تم الرفع من 10 إلى 30 لضمان سلاسة الاستخدام ومنع الحظر أثناء التجربة
    
class ExamGenerationDailyThrottle(UserRateThrottle):
    """
    Custom throttle to limit how many exams a user can generate per day.
    """
    rate = '200/day' # limit to 200 exams per day

class AuthThrottle(UserRateThrottle):
    """
    حماية تسجيل الدخول وإنشاء الحساب من هجمات التخمين (Brute Force).
    """
    rate = '10/minute'
