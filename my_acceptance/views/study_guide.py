from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ..models import CollegeStudyGuide


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def college_study_guide(request):
    """جلب أدلة المراجعة لكلية محددة (أو لمادة محددة في كلية)"""
    college_id = request.query_params.get('college')
    subject_id = request.query_params.get('subject')

    if not college_id:
        return Response({'error': 'يرجى تحديد الكلية'}, status=status.HTTP_400_BAD_REQUEST)

    qs = CollegeStudyGuide.objects.filter(college_id=college_id, is_active=True)

    if subject_id:
        qs = qs.filter(subject_id=subject_id)

    guides = []
    for g in qs.select_related('subject'):
        # تحويل المحتوى إلى أقسام منسقة
        sections = _parse_guide_content(g.content)
        guides.append({
            'id': g.id,
            'title': g.title,
            'subject_id': g.subject_id,
            'subject_name': g.subject.name,
            'sections': sections,
            'updated_at': g.updated_at.isoformat(),
        })

    return Response(guides)


def _parse_guide_content(content):
    """
    تحويل نص الدليل إلى أقسام منظمة بناءً على الرموز التعبيرية.
    يدعم التنسيق المستخدم:
    🎯 عنوان القسم
    🔥 عنوان آخر
    - نقطة فرعية
    👉 توصية
    """
    lines = content.split('\n')
    sections = []
    current_section = None

    # الرموز التي تبدأ بها العناوين
    section_emojis = ['🎯', '🔥', '⚠️', '📊', '🏥', '⚗️', '⚡️']

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # تحقق إذا كان السطر عنوان قسم جديد
        is_section_header = any(stripped.startswith(e) for e in section_emojis)

        if is_section_header:
            if current_section:
                sections.append(current_section)
            current_section = {
                'header': stripped,
                'items': [],
            }
        elif current_section is not None:
            current_section['items'].append(stripped)
        else:
            # سطر قبل أول قسم (مثل عنوان الكلية الرئيسي)
            if not sections and current_section is None:
                current_section = {
                    'header': stripped,
                    'items': [],
                }

    if current_section:
        sections.append(current_section)

    return sections
