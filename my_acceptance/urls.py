from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UniversityViewSet,
    CollegeViewSet,
    SubjectViewSet,
    PDFResourceViewSet,
    TestSessionViewSet,
    generate_exam,
    submit_exam,
    login_with_device,
    register_user,
    logout_user,
    activate_premium,
    available_templates,
    list_favorites,
    toggle_favorite,
    favorites_count,
    performance_stats,
    flashcard_decks,
    flashcard_due_cards,
    flashcard_review,
    flashcard_summary,
    question_analysis,
    college_study_guide,
    set_target_college,
    NotificationListView,
)

router = DefaultRouter()
router.register(r'universities', UniversityViewSet)
router.register(r'colleges', CollegeViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'pdf-resources', PDFResourceViewSet)
router.register(r'test-sessions', TestSessionViewSet, basename='test-sessions')

urlpatterns = [
    path('', include(router.urls)),
    # Auth
    path('auth/register/', register_user, name='register'),
    path('auth/login/', login_with_device, name='login-with-device'),
    path('auth/logout/', logout_user, name='logout'),
    path('auth/activate/', activate_premium, name='activate_premium'),
    # Exams
    path('generate-exam/', generate_exam, name='generate_exam'),
    path('submit-exam/', submit_exam, name='submit_exam'),
    path('available-templates/', available_templates, name='available_templates'),
    # Favorites
    path('favorites/', list_favorites, name='list_favorites'),
    path('favorites/toggle/', toggle_favorite, name='toggle_favorite'),
    path('favorites/count/', favorites_count, name='favorites_count'),
    # Performance
    path('performance/', performance_stats, name='performance_stats'),
    # Flashcards
    path('flashcards/decks/', flashcard_decks, name='flashcard_decks'),
    path('flashcards/due/', flashcard_due_cards, name='flashcard_due_cards'),
    path('flashcards/review/', flashcard_review, name='flashcard_review'),
    path('flashcards/summary/', flashcard_summary, name='flashcard_summary'),
    # Analysis
    path('question-analysis/', question_analysis, name='question_analysis'),
    # Study Guide
    path('study-guide/', college_study_guide, name='college_study_guide'),
    # Target College
    path('set-target-college/', set_target_college, name='set_target_college'),
    # Notifications
    path('notifications/', NotificationListView.as_view(), name='notifications_list'),
]
