from rest_framework import viewsets, permissions
from django.db.models import Q
from ..models import University, College, Subject, PDFResource
from ..serializers import UniversitySerializer, CollegeSerializer, SubjectSerializer, PDFResourceSerializer

class UniversityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = University.objects.filter(is_active=True).order_by('id')
    serializer_class = UniversitySerializer
    permission_classes = [permissions.AllowAny]

class CollegeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = College.objects.filter(is_active=True).order_by('id')
    serializer_class = CollegeSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        university_id = self.request.query_params.get('university')
        category = self.request.query_params.get('category')
        search = self.request.query_params.get('search')
        if university_id:
            queryset = queryset.filter(university_id=university_id)
        if category:
            queryset = queryset.filter(category=category)
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset

class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Subject.objects.filter(is_active=True).order_by('id')
    serializer_class = SubjectSerializer
    permission_classes = [permissions.AllowAny]



class PDFResourceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PDFResource.objects.all().order_by('-year')
    serializer_class = PDFResourceSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        college_id = self.request.query_params.get('college')
        subject_id = self.request.query_params.get('subject')
        year = self.request.query_params.get('year')
        university_id = self.request.query_params.get('university')
        if college_id:
            try:
                college = College.objects.get(id=college_id)
                related_uni_ids = College.objects.filter(code=college.code).values_list('university_id', flat=True)
                queryset = queryset.filter(
                    Q(college__code=college.code) |
                    Q(college__isnull=True, university_id__in=related_uni_ids)
                )
            except College.DoesNotExist:
                queryset = queryset.filter(college_id=college_id)
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        if year:
            queryset = queryset.filter(year=year)
        if university_id:
            queryset = queryset.filter(college__university_id=university_id)
        return queryset
