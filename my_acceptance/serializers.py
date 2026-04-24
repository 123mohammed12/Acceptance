import random
from rest_framework import serializers
from .models import University, College, Subject, Question, Option, PDFResource, TestSession, StudentAnswer, FavoriteQuestion, Deck, Flashcard

class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = '__all__'

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'

class CollegeSerializer(serializers.ModelSerializer):
    university_name = serializers.ReadOnlyField(source='university.name')
    subjects = SubjectSerializer(many=True, read_only=True)

    class Meta:
        model = College
        fields = ['id', 'university', 'university_name', 'name', 'code', 'category', 'icon_name', 'subjects', 'high_school_weight', 'exam_weight', 'is_active']

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'identifier', 'text', 'is_correct']

class QuestionSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    source_university_name = serializers.ReadOnlyField(source='source_university.name')
    subject_name = serializers.ReadOnlyField(source='subject.name')

    class Meta:
        model = Question
        fields = ['id', 'subject', 'subject_name', 'grade_level', 'unit', 'text', 'explanation',
                  'image', 'exam_year', 'source_university', 'source_university_name',
                  'options', 'times_appeared', 'is_favorited']

    def get_options(self, obj):
        opts = list(obj.options.all())
        # خلط الخيارات إذا طُلب ذلك (يمرر عبر context)
        if self.context.get('shuffle_options', True):
            random.shuffle(opts)
        return OptionSerializer(opts, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return FavoriteQuestion.objects.filter(user=request.user, question=obj).exists()
        return False

class PDFResourceSerializer(serializers.ModelSerializer):
    college_name = serializers.ReadOnlyField(source='college.name')
    subject_name = serializers.ReadOnlyField(source='subject.name')
    university_name = serializers.ReadOnlyField(source='college.university.name')

    class Meta:
        model = PDFResource
        fields = ['id', 'college', 'college_name', 'subject', 'subject_name',
                  'university_name', 'title', 'resource_type', 'year', 'file']

class StudentAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAnswer
        fields = '__all__'

class TestSessionSerializer(serializers.ModelSerializer):
    student_answers = StudentAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = TestSession
        fields = '__all__'

class FavoriteQuestionSerializer(serializers.ModelSerializer):
    question_text = serializers.ReadOnlyField(source='question.text')
    question_id = serializers.ReadOnlyField(source='question.id')
    subject_id = serializers.ReadOnlyField(source='question.subject.id')
    subject_name = serializers.ReadOnlyField(source='question.subject.name')
    exam_year = serializers.ReadOnlyField(source='question.exam_year')

    class Meta:
        model = FavoriteQuestion
        fields = ['id', 'question_id', 'question_text', 'subject_id', 'subject_name', 'exam_year', 'created_at']


# ── البطاقات التعليمية ──

class DeckSerializer(serializers.ModelSerializer):
    subject_name = serializers.ReadOnlyField(source='subject.name')
    card_count = serializers.SerializerMethodField()

    class Meta:
        model = Deck
        fields = ['id', 'name', 'subject', 'subject_name', 'description', 'card_count']

    def get_card_count(self, obj):
        return obj.cards.count()


class FlashcardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flashcard
        fields = ['id', 'front', 'back', 'deck']
