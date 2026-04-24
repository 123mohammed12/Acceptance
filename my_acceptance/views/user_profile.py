from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Count, Avg, Case, When
from ..models import Question, FavoriteQuestion, TestSession, StudentAnswer
from ..serializers import FavoriteQuestionSerializer

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_favorites(request):
    subject_id = request.query_params.get('subject')
    favs = FavoriteQuestion.objects.filter(user=request.user).select_related('question', 'question__subject').order_by('-created_at')
    
    if subject_id:
        favs = favs.filter(question__subject_id=subject_id)
        
    serializer = FavoriteQuestionSerializer(favs, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_favorite(request):
    question_id = request.data.get('question_id')
    if not question_id:
        return Response({'error': 'يرجى تحديد رقم السؤال'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        return Response({'error': 'السؤال غير موجود'}, status=status.HTTP_404_NOT_FOUND)

    fav, created = FavoriteQuestion.objects.get_or_create(user=request.user, question=question)
    if not created:
        fav.delete()
        return Response({'status': 'removed', 'is_favorited': False})
    return Response({'status': 'added', 'is_favorited': True})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def favorites_count(request):
    counts = FavoriteQuestion.objects.filter(user=request.user).values(
        'question__subject__id', 'question__subject__name',
        'question__source_college__id', 'question__source_college__name'
    ).annotate(count=Count('id')).order_by('-count')

    result = []
    total = 0
    for item in counts:
        c = item['count']
        total += c
        result.append({
            'subject_id': item['question__subject__id'],
            'subject_name': item['question__subject__name'],
            'college_id': item['question__source_college__id'],
            'college_name': item['question__source_college__name'],
            'count': c,
        })
    return Response({'total': total, 'by_subject': result})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def performance_stats(request):
    sessions = TestSession.objects.filter(student=request.user)
    total_exams = sessions.count()
    if total_exams == 0:
        return Response({
            'total_exams': 0, 'overall_average': 0, 'by_subject': [],
            'recent_scores': [], 'favorites_count': 0,
            'total_questions_answered': 0, 'total_correct': 0,
        })

    overall_avg = sessions.aggregate(avg=Avg('score_percentage'))['avg'] or 0
    subject_stats = StudentAnswer.objects.filter(
        session__student=request.user
    ).values(
        'question__subject__id', 'question__subject__name'
    ).annotate(
        total=Count('id'),
        correct=Count(Case(When(is_correct=True, then=1))),
    ).order_by('-total')

    by_subject = []
    for s in subject_stats:
        total = s['total']
        correct = s['correct']
        pct = round((correct / total * 100), 1) if total > 0 else 0
        by_subject.append({
            'subject_id': s['question__subject__id'],
            'subject_name': s['question__subject__name'],
            'total_questions': total,
            'correct_answers': correct,
            'percentage': pct,
        })

    recent = list(sessions.order_by('-created_at')[:10].values('score_percentage', 'created_at', 'test_type'))
    favs = FavoriteQuestion.objects.filter(user=request.user).count()
    total_q = StudentAnswer.objects.filter(session__student=request.user).count()
    total_correct = StudentAnswer.objects.filter(session__student=request.user, is_correct=True).count()

    return Response({
        'total_exams': total_exams,
        'overall_average': round(overall_avg, 1),
        'by_subject': by_subject,
        'recent_scores': recent,
        'favorites_count': favs,
        'total_questions_answered': total_q,
        'total_correct': total_correct,
    })
