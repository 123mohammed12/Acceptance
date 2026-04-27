from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from django.db.models import Count, Avg, Q
import random

from ..models import College, Subject, Question, Option, TestSession, StudentAnswer, UserProfile
from ..serializers import TestSessionSerializer, QuestionSerializer
from ..throttling import ExamGenerationThrottle, ExamGenerationDailyThrottle

class TestSessionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TestSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TestSession.objects.filter(student=self.request.user).order_by('-created_at')

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def available_templates(request):
    college_id = request.query_params.get('college')
    subject_id = request.query_params.get('subject')
    exam_year = request.query_params.get('exam_year')
    source_uni = request.query_params.get('source_university')

    if not college_id:
        return Response({'error': 'يرجى تحديد الكلية'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        college = College.objects.get(id=college_id)
    except College.DoesNotExist:
        return Response({'error': 'الكلية غير موجودة'}, status=status.HTTP_404_NOT_FOUND)

    college_code = college.code
    related_uni_ids = College.objects.filter(code=college_code).values_list('university_id', flat=True)

    qs = Question.objects.filter(
        exam_year__isnull=False,
        source_university__isnull=False,
    )

    qs = qs.filter(
        Q(source_college__code=college_code) |
        Q(source_college__isnull=True, source_university_id__in=related_uni_ids)
    )

    if subject_id:
        qs = qs.filter(subject_id=subject_id)
    if exam_year:
        qs = qs.filter(exam_year=exam_year)
    if source_uni:
        qs = qs.filter(source_university_id=source_uni)

    templates = qs.values(
        'subject__id', 'subject__name',
        'exam_year',
        'source_university__id', 'source_university__name',
    ).annotate(
        question_count=Count('id')
    ).order_by('-exam_year', 'subject__name')

    result = []
    for t in templates:
        result.append({
            'subject_id': t['subject__id'],
            'subject_name': t['subject__name'],
            'exam_year': t['exam_year'],
            'university_id': t['source_university__id'],
            'university_name': t['source_university__name'],
            'question_count': t['question_count'],
        })

    return Response(result)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([ExamGenerationThrottle, ExamGenerationDailyThrottle])
def generate_exam(request):
    test_type = request.query_params.get('test_type')
    college_id = request.query_params.get('college')
    subject_id = request.query_params.get('subject')
    grade_level = request.query_params.get('grade_level')
    unit_num = request.query_params.get('unit')
    exam_year = request.query_params.get('exam_year')
    source_uni = request.query_params.get('source_university')
    years_str = request.query_params.get('years')
    limit = min(int(request.query_params.get('limit', 50)), 100) # منع السحب بكميات ضخمة
    shuffle_q = request.query_params.get('shuffle', 'true') == 'true'
    exam_category = request.query_params.get('exam_category', 'past_exam')

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if not profile.is_premium:
        if exam_category == 'past_exam':
            if profile.free_past_exam_trials >= 2:
                return Response({
                    'detail': 'للحصول على كافه مزايا التطبيق يرجى تفعيل النسخة.',
                    'code': 'ACTIVATION_REQUIRED'
                }, status=status.HTTP_403_FORBIDDEN)
            profile.free_past_exam_trials += 1
            profile.save()
        elif exam_category == 'challenge':
            if profile.free_challenge_trials >= 2:
                return Response({
                    'detail': 'للحصول على كافه مزايا التطبيق يرجى تفعيل النسخة.',
                    'code': 'ACTIVATION_REQUIRED'
                }, status=status.HTTP_403_FORBIDDEN)
            profile.free_challenge_trials += 1
            profile.save()

    questions = []

    if test_type == 'favorites' and subject_id:
        from ..models import FavoriteQuestion
        fav_ids = FavoriteQuestion.objects.filter(
            user=request.user, 
            question__subject_id=subject_id
        ).values_list('question_id', flat=True)
        qs = list(Question.objects.filter(id__in=fav_ids))
        if shuffle_q:
            random.shuffle(qs)
        questions = qs[:limit]

    elif test_type == 'year_sim' and subject_id:
        filters = {'subject_id': subject_id}
        if exam_year:
            filters['exam_year'] = exam_year
        if source_uni:
            filters['source_university_id'] = source_uni
            
        qs = Question.objects.filter(**filters)
        
        if college_id:
            try:
                college = College.objects.get(id=college_id)
                related_uni_ids = College.objects.filter(code=college.code).values_list('university_id', flat=True)
                qs = qs.filter(
                    Q(source_college__code=college.code) |
                    Q(source_college__isnull=True, source_university_id__in=related_uni_ids)
                )
            except College.DoesNotExist:
                pass

                
        qs_list = list(qs)
        if shuffle_q:
            random.shuffle(qs_list)
        questions = qs_list[:limit]

    elif test_type == 'mock' and college_id:
        college = College.objects.filter(id=college_id).first()
        if not college:
            return Response({'error': 'الكلية غير موجودة'}, status=status.HTTP_404_NOT_FOUND)
            
        subjects = Subject.objects.filter(required_for_colleges__code=college.code).distinct()
        all_questions = []
        questions_per_subject = limit // subjects.count() if subjects.exists() else 20
        
        for sub in subjects:
            sub_qs = list(Question.objects.filter(subject=sub, source_college__code=college.code))
            if not sub_qs:
                 sub_qs = list(Question.objects.filter(subject=sub))
            random.shuffle(sub_qs)
            all_questions.extend(sub_qs[:questions_per_subject])
            
        if shuffle_q:
            random.shuffle(all_questions)
        questions = all_questions[:limit]

    elif test_type == 'unit' and subject_id and unit_num:
        filters = {'subject_id': subject_id, 'unit': unit_num}
        if grade_level:
            filters['grade_level'] = grade_level
        qs = list(Question.objects.filter(**filters))
        if shuffle_q:
            random.shuffle(qs)
        questions = qs[:limit]

    elif test_type == 'most_repeated':
        if subject_id:
            # فلترة حسب المادة (السلوك الأصلي)
            filters = {'subject_id': subject_id}
            if unit_num:
                filters['unit'] = unit_num
            qs = list(Question.objects.filter(**filters).order_by('-times_appeared'))
            questions = qs[:limit]
        elif college_id:
            # تجميع الأسئلة الأكثر تكراراً لجميع مواد الكلية
            try:
                college = College.objects.get(id=college_id)
                college_subject_ids = college.subjects.values_list('id', flat=True)
                qs = list(
                    Question.objects.filter(
                        subject_id__in=college_subject_ids,
                        times_appeared__gt=0
                    ).order_by('-times_appeared')
                )
                questions = qs[:limit]
            except College.DoesNotExist:
                pass


    elif test_type == 'bank' and subject_id and years_str:
        try:
            years_list = [int(y.strip()) for y in years_str.split(',')]
        except ValueError:
            return Response({'error': 'صيغة السنوات غير صحيحة.'}, status=status.HTTP_400_BAD_REQUEST)
        qs = list(Question.objects.filter(subject_id=subject_id, exam_year__in=years_list))
        if shuffle_q:
            random.shuffle(qs)
        questions = qs[:limit]

    elif test_type == 'subject_all' and subject_id:
        qs = list(Question.objects.filter(subject_id=subject_id))
        if shuffle_q:
            random.shuffle(qs)
        questions = qs[:limit]

    elif test_type == 'favorites':
        from ..models import FavoriteQuestion
        fav_q_ids = FavoriteQuestion.objects.filter(user=request.user).values_list('question_id', flat=True)
        qs = list(Question.objects.filter(id__in=fav_q_ids))
        if subject_id:
            qs = [q for q in qs if q.subject_id == int(subject_id)]
        if shuffle_q:
            random.shuffle(qs)
        questions = qs[:limit]

    elif test_type == 'book' and subject_id and grade_level:
        qs = list(Question.objects.filter(subject_id=subject_id, grade_level=grade_level))
        if shuffle_q:
            random.shuffle(qs)
        questions = qs[:40]

    shuffle_opts = request.query_params.get('shuffle_options', 'true') == 'true'
    serializer = QuestionSerializer(questions, many=True, context={'request': request, 'shuffle_options': shuffle_opts})
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def submit_exam(request):
    data = request.data
    test_type = data.get('test_type')
    college_id = data.get('college_id')
    exam_mode = data.get('exam_mode', 'instant')
    answers = data.get('answers', [])

    total_questions = len(answers)
    correct_count = 0

    for ans in answers:
        option_id = ans.get('option_id')
        if option_id:
            try:
                opt = Option.objects.get(id=option_id)
                if opt.is_correct:
                    correct_count += 1
            except Option.DoesNotExist:
                pass

    score_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
    college = College.objects.filter(id=college_id).first() if college_id else None

    session = TestSession.objects.create(
        student=request.user,
        college=college,
        test_type=test_type,
        exam_mode=exam_mode,
        total_questions=total_questions,
        correct_answers_count=correct_count,
        score_percentage=score_percentage
    )

    for ans in answers:
        q_id = ans.get('question_id')
        opt_id = ans.get('option_id')
        if q_id:
            try:
                opt = Option.objects.get(id=opt_id) if opt_id else None
                is_correct = opt.is_correct if opt else False
                StudentAnswer.objects.create(
                    session=session,
                    question_id=q_id,
                    selected_option=opt,
                    is_correct=is_correct
                )
            except Exception:
                continue

    serializer = TestSessionSerializer(session)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def question_analysis(request):
    subject_id = request.query_params.get('subject')
    college_id = request.query_params.get('college')
    exam_year = request.query_params.get('exam_year')

    if not subject_id:
        return Response({'error': 'يرجى تحديد المادة'}, status=status.HTTP_400_BAD_REQUEST)

    qs = Question.objects.filter(subject_id=subject_id)

    if college_id:
        try:
            college = College.objects.get(id=college_id)
            related_uni_ids = College.objects.filter(code=college.code).values_list('university_id', flat=True)
            qs = qs.filter(
                Q(source_college__code=college.code) |
                Q(source_college__isnull=True, source_university_id__in=related_uni_ids)
            )
        except College.DoesNotExist:
            pass

    if exam_year:
        qs = qs.filter(exam_year=exam_year)

    by_unit = list(qs.values('unit', 'grade_level').annotate(count=Count('id'), avg_times=Avg('times_appeared')).order_by('-count'))
    grade_labels = {9: 'التاسع', 10: 'أول ثانوي', 11: 'ثاني ثانوي', 12: 'ثالث ثانوي'}
    for item in by_unit:
        item['grade_name'] = grade_labels.get(item['grade_level'], f"الصف {item['grade_level']}")
    by_grade = list(qs.values('grade_level').annotate(count=Count('id')).order_by('grade_level'))
    grade_labels = {9: 'التاسع', 10: 'أول ثانوي', 11: 'ثاني ثانوي', 12: 'ثالث ثانوي'}
    for item in by_grade:
        item['grade_name'] = grade_labels.get(item['grade_level'], f"الصف {item['grade_level']}")

    available_years = list(qs.filter(exam_year__isnull=False).values_list('exam_year', flat=True).distinct().order_by('-exam_year'))
    top_repeated = list(qs.filter(times_appeared__gt=1).order_by('-times_appeared').values('id', 'text', 'unit', 'grade_level', 'times_appeared')[:10])

    return Response({
        'total_questions': qs.count(),
        'total_units': qs.values('unit').distinct().count(),
        'by_unit': by_unit,
        'by_grade': by_grade,
        'available_years': available_years,
        'top_repeated': top_repeated,
    })
