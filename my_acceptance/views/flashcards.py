from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone

from ..models import UserProfile, Deck, Flashcard, UserFlashcardProgress
from ..serializers import DeckSerializer, FlashcardSerializer

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def flashcard_decks(request):
    """
    عرض مجموعات البطاقات المتاحة لمادة معينة.
    فلتر: ?subject=<id>
    """
    subject_id = request.query_params.get('subject')
    qs = Deck.objects.all()
    if subject_id:
        qs = qs.filter(subject_id=subject_id)
    serializer = DeckSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def flashcard_due_cards(request):
    """
    جلب البطاقات المستحقة للمراجعة اليوم لمجموعة معينة.
    فلتر: ?deck=<id>
    ميزة تتطلب تفعيل النسخة الكاملة.
    """
    # فحص الاشتراك
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if not profile.is_premium:
        return Response({
            'detail': 'للحصول على كافه مزايا التطبيق يرجى تفعيل النسخة.',
            'code': 'ACTIVATION_REQUIRED'
        }, status=status.HTTP_403_FORBIDDEN)

    deck_id = request.query_params.get('deck')
    today = timezone.now().date()
    
    if deck_id:
        cards = Flashcard.objects.filter(deck_id=deck_id)
    else:
        cards = Flashcard.objects.all()

    due_cards = []
    new_count = 0
    due_count = 0
    learn_count = 0

    for card in cards:
        progress, created = UserFlashcardProgress.objects.get_or_create(
            user=request.user, flashcard=card
        )

        if created or progress.repetitions == 0:
            new_count += 1
            due_cards.append((card, progress))
        elif progress.next_review_date <= today:
            if progress.interval < 1:
                learn_count += 1
            else:
                due_count += 1
            due_cards.append((card, progress))

    response_data = []
    for card, progress in due_cards:
        card_data = FlashcardSerializer(card).data
        card_data['projected_intervals'] = {
            'hard': progress.simulate_sm2(2),
            'good': progress.simulate_sm2(3),
            'easy': progress.simulate_sm2(5),
        }
        response_data.append(card_data)

    return Response({
        'session_stats': {
            'new_count': new_count,
            'learn_count': learn_count,
            'due_count': due_count,
            'total_due': len(due_cards),
        },
        'total_count': cards.count(),
        'cards': response_data,
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def flashcard_review(request):
    """
    تسجيل مراجعة بطاقة وتطبيق خوارزمية SM-2.
    المطلوب: flashcard_id, quality (hard/good/easy)
    """
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if not profile.is_premium:
        return Response({
            'detail': 'للحصول على كافه مزايا التطبيق يرجى تفعيل النسخة.',
            'code': 'ACTIVATION_REQUIRED'
        }, status=status.HTTP_403_FORBIDDEN)

    flashcard_id = request.data.get('flashcard_id')
    quality_str = request.data.get('quality', '').lower()

    quality_map = {'hard': 2, 'good': 3, 'easy': 5}
    quality = quality_map.get(quality_str)

    if not flashcard_id or quality is None:
        return Response({'error': 'يرجى إرسال flashcard_id و quality (hard/good/easy)'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        card = Flashcard.objects.get(id=flashcard_id)
    except Flashcard.DoesNotExist:
        return Response({'error': 'البطاقة غير موجودة'}, status=status.HTTP_404_NOT_FOUND)

    progress, _ = UserFlashcardProgress.objects.get_or_create(
        user=request.user,
        flashcard=card,
    )

    progress.apply_sm2(quality)

    return Response({
        'status': 'ok',
        'next_review_date': str(progress.next_review_date),
        'interval': progress.interval,
        'ease_factor': round(progress.ease_factor, 2),
        'repetitions': progress.repetitions,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def flashcard_summary(request):
    """إحصائيات سريعة للبطاقات: كم بطاقة متبقية للمراجعة اليوم"""
    today = timezone.now().date()
    due_count = UserFlashcardProgress.objects.filter(
        user=request.user,
        next_review_date__lte=today
    ).count()
    
    return Response({
        'due_today_count': due_count,
    })
