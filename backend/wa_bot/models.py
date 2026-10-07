from django.db import models
from core.models import User


class WhatsAppMessageLog(models.Model):
    class Direction(models.TextChoices):
        OUT = 'OUT', 'Outbound'
        IN = 'IN', 'Inbound'

    class MessageType(models.TextChoices):
        ATTENDANCE_ALERT = 'ATTENDANCE_ALERT', 'Attendance Alert'
        DEADLINE_REMINDER = 'DEADLINE_REMINDER', 'Deadline Reminder'
        GRADE_ALERT = 'GRADE_ALERT', 'Grade Alert'
        MENU_QUERY = 'MENU_QUERY', 'Menu Query'
        OTHER = 'OTHER', 'Other'

    recipient = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='wa_messages'
    )
    phone_number = models.CharField(max_length=20)
    direction = models.CharField(max_length=3, choices=Direction.choices)
    message_type = models.CharField(
        max_length=30, choices=MessageType.choices, default=MessageType.OTHER
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.direction}] {self.phone_number} — {self.message_type} @ {self.created_at:%Y-%m-%d %H:%M}"
