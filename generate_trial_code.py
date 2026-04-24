import os
import django

# إعداد بيئة دجانغو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from my_acceptance.models import ActivationCode

def create_trial_code():
    obj, plain_code = ActivationCode.generate(
        duration_days=30,
        admin_name='Antigravity AI',
        note='كود تجريبي للاختبار'
    )
    print(f"\n======================================")
    print(f"SUCCESS: Activation code created!")
    print(f"Code: {plain_code}")
    print(f"Duration: {obj.duration_days} days")
    print(f"======================================\n")

if __name__ == "__main__":
    create_trial_code()
