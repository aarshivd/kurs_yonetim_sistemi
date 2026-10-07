from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Assignment, ParentStudent
from wa_bot.services import send_whatsapp_message

class Command(BaseCommand):
    help = "Yarına (24 saat içine) kadar teslim edilmesi gereken ödevleri öğrencilere ve velilere WhatsApp'tan hatırlatır."

    def handle(self, *args, **options):
        now = timezone.now()
        tomorrow = now + timedelta(hours=24)
        
        # Gelecek 24 saat içinde bitecek ve henüz süresi geçmemiş ödevler
        soon = Assignment.objects.filter(
            deadline__lte=tomorrow,
            deadline__gte=now
        )
        
        count = 0
        for assignment in soon:
            text = f"Hatırlatma: '{assignment.title}' ödevinin son teslim tarihi yaklaşıyor ({assignment.deadline.strftime('%d.%m.%Y %H:%M')})."
            
            for student in assignment.classroom.students.all():
                # Öğrenciye gönder
                if student.phone_number:
                    send_whatsapp_message(
                        phone_number=student.phone_number, 
                        text=text, 
                        recipient=student,
                        message_type='DEADLINE_REMINDER'
                    )
                    count += 1
                    
                # Velisine (veya velilerine) gönder
                for link in ParentStudent.objects.filter(student=student):
                    if link.parent.phone_number:
                        parent_text = f"Sayın Veli, öğrenciniz {student.get_full_name() or student.username}'in '{assignment.title}' ödevinin son teslim tarihi yaklaşıyor."
                        send_whatsapp_message(
                            phone_number=link.parent.phone_number, 
                            text=parent_text,
                            recipient=link.parent, 
                            message_type='DEADLINE_REMINDER'
                        )
                        count += 1
                        
        self.stdout.write(self.style.SUCCESS(f"{count} adet hatırlatma mesajı gönderildi."))
