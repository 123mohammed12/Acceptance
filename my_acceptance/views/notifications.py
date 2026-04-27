from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from ..models import AppNotification
from ..serializers import AppNotificationSerializer

class NotificationListView(generics.ListAPIView):
    """
    يعيد قائمة بجميع الإشعارات الفعالة، مرتبة من الأحدث للأقدم.
    """
    serializer_class = AppNotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AppNotification.objects.filter(is_active=True)
