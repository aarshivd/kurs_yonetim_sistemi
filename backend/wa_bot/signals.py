from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Attendance, ParentStudent
from .services import send_whatsapp_message

@receiver(post_save, sender=Attendance)
def notify_parent_on_absence(sender, instance, created, **kwargs):
    if not instance.is_present:
        for link in ParentStudent.objects.filter(student=instance.student):
            parent = link.parent
            if parent.phone_number:
                student_name = instance.student.get_full_name() or instance.student.username
                text = f"Sayın Veli, {student_name} bugünkü derse katılmadı."
                send_whatsapp_message(
                    phone_number=parent.phone_number,
                    text=text,
                    recipient=parent,
                    message_type='ATTENDANCE_ALERT'
                )
