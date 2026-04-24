from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
import re

from ..models import UserProfile, ActivationCode, College

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_user(request):
    """
    إنشاء حساب جديد.
    المطلوب: username + password + device_id
    اختياري: email, phone_number, full_name
    """
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '').strip()
    email = request.data.get('email', '').strip()
    phone = request.data.get('phone_number', '').strip()
    full_name = request.data.get('full_name', '').strip()
    device_id = request.data.get('device_id', '').strip()

    # التحقق من الحقول الإجبارية
    if not username or not password or not device_id:
        return Response({'detail': 'يرجى ملء جميع الحقول المطلوبة (اسم المستخدم، كلمة المرور، بصمة الجهاز).'}, status=status.HTTP_400_BAD_REQUEST)

    # تحقق اسم المستخدم (أحرف + أرقام + _ فقط)
    if not re.match(r'^[a-zA-Z0-9_]{3,30}$', username):
        return Response({'detail': 'اسم المستخدم يجب أن يكون 3-30 حرف (أحرف إنجليزية وأرقام و _ فقط).'}, status=status.HTTP_400_BAD_REQUEST)

    if len(password) < 6:
        return Response({'detail': 'كلمة المرور يجب أن تكون 6 أحرف على الأقل.'}, status=status.HTTP_400_BAD_REQUEST)

    # تحقق التكرار
    if User.objects.filter(username=username).exists():
        return Response({'detail': 'اسم المستخدم مستخدم بالفعل. جرّب اسماً آخر.'}, status=status.HTTP_409_CONFLICT)

    if email and User.objects.filter(email=email).exists():
        return Response({'detail': 'يوجد حساب مسجل بهذا البريد الإلكتروني.'}, status=status.HTTP_409_CONFLICT)

    if phone and UserProfile.objects.filter(phone_number=phone).exists():
        return Response({'detail': 'يوجد حساب مسجل بهذا الرقم بالفعل.'}, status=status.HTTP_409_CONFLICT)

    # إنشاء المستخدم
    user = User.objects.create_user(
        username=username,
        password=password,
        email=email,
        first_name=full_name,
    )

    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.phone_number = phone if phone else None
    profile.device_id = device_id
    profile.save()

    refresh = RefreshToken.for_user(user)
    return Response({
        'detail': 'تم إنشاء الحساب بنجاح!',
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'is_premium': False,
        'full_name': full_name,
        'free_past_exam_remaining': 2,
        'free_challenge_remaining': 2,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_with_device(request):
    """
    تسجيل الدخول باسم المستخدم أو البريد أو رقم الهاتف مع بصمة الجهاز.
    """
    identifier = request.data.get('identifier', '').strip()
    password = request.data.get('password', '').strip()
    device_id = request.data.get('device_id', '').strip()

    if not identifier or not password or not device_id:
        return Response({'detail': 'يرجى توفير بيانات الدخول وبصمة الجهاز.'}, status=status.HTTP_400_BAD_REQUEST)

    # البحث باسم المستخدم أولاً، ثم الإيميل، ثم رقم الهاتف
    user = User.objects.filter(username=identifier).first()
    if not user:
        user = User.objects.filter(email=identifier).first()
    if not user:
        profile_match = UserProfile.objects.filter(phone_number=identifier).first()
        if profile_match:
            user = profile_match.user

    if not user or not user.check_password(password):
        return Response({'detail': 'بيانات الدخول غير صحيحة.'}, status=status.HTTP_401_UNAUTHORIZED)

    profile, created = UserProfile.objects.get_or_create(user=user)

    if profile.device_id and profile.device_id != device_id:
        return Response({
            'detail': 'هذا الحساب مسجّل دخوله حالياً من جهاز آخر. يرجى تسجيل الخروج من الجهاز الآخر أولاً.',
            'code': 'DEVICE_CONFLICT'
        }, status=status.HTTP_403_FORBIDDEN)

    profile.device_id = device_id
    profile.save()

    refresh = RefreshToken.for_user(user)
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'is_premium': profile.is_premium,
        'full_name': user.first_name,
        'free_past_exam_remaining': max(0, 2 - profile.free_past_exam_trials),
        'free_challenge_remaining': max(0, 2 - profile.free_challenge_trials),
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_user(request):
    """
    تسجيل الخروج: يمسح بصمة الجهاز من الحساب.
    """
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.device_id = None
    profile.save()
    return Response({'detail': 'تم تسجيل الخروج بنجاح. يمكنك الآن الدخول من أي جهاز.'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def activate_premium(request):
    """
    تفعيل الاشتراك بكود تفعيل.
    الكود يُستخدم مرة واحدة فقط.
    يتم مقارنة SHA-256 hash بدل الكود الأصلي للحماية.
    """
    code_input = request.data.get('code', '').strip().upper()

    if not code_input:
        return Response({'detail': 'يرجى إدخال كود التفعيل.'}, status=status.HTTP_400_BAD_REQUEST)

    if len(code_input) < 6 or len(code_input) > 16:
        return Response({'detail': 'كود غير صالح.'}, status=status.HTTP_400_BAD_REQUEST)

    code_hash = ActivationCode.hash_code(code_input)
    activation = ActivationCode.objects.filter(code_hash=code_hash, is_used=False).first()

    if not activation:
        return Response({'detail': 'كود التفعيل غير صالح أو مُستخدم مسبقاً.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        activation.activate_for_user(request.user)
    except ValueError as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'detail': 'تم تفعيل اشتراكك بنجاح! 🎉 يمكنك الآن الوصول لجميع الاختبارات.',
        'is_premium': True,
        'duration_days': activation.duration_days,
    })


