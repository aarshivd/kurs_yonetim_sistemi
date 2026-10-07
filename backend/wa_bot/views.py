import os
import json
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from core.models import User, Schedule, Attendance, StudentAssignment, Grade, Announcement, ParentStudent
from .models import WhatsAppMessageLog
from .services import send_whatsapp_message

logger = logging.getLogger(__name__)

MENU_TEXT = ("Merhaba! 👋\n1) Ders programım\n2) Devamsızlık durumum\n"
             "3) Ödevlerim\n4) Notlarım\n5) Duyurular")

def build_reply(user, message_text):
    students = []
    if user.role == User.Role.PARENT:
        students = [link.student for link in ParentStudent.objects.filter(parent=user)]
    elif user.role == User.Role.STUDENT:
        students = [user]
        
    if not students:
        return "Sisteme kayıtlı öğrenci kaydınız bulunamadı."

    reply_parts = []
    
    if message_text == '1':
        for student in students:
            schedules = Schedule.objects.filter(classroom__students=student)
            if schedules.exists():
                text = f"📚 *{student.get_full_name() or student.username} Ders Programı:*\n"
                for sch in schedules:
                    text += f"- {sch.get_day_of_week_display()}: {sch.start_time.strftime('%H:%M')} - {sch.end_time.strftime('%H:%M')} ({sch.classroom.name})\n"
                reply_parts.append(text)
            else:
                reply_parts.append(f"*{student.get_full_name() or student.username}* için ders programı bulunamadı.")
        return "\n".join(reply_parts)
        
    elif message_text == '2':
        for student in students:
            attendances = Attendance.objects.filter(student=student).order_by('-session__date')[:5]
            if attendances.exists():
                text = f"📅 *{student.get_full_name() or student.username} Devamsızlık (Son 5):*\n"
                for att in attendances:
                    status = "✅ Katıldı" if att.is_present else "❌ Katılmadı"
                    text += f"- {att.session.date.strftime('%d.%m.%Y')}: {status}\n"
                reply_parts.append(text)
            else:
                reply_parts.append(f"*{student.get_full_name() or student.username}* için devamsızlık kaydı bulunamadı.")
        return "\n".join(reply_parts)
        
    elif message_text == '3':
        for student in students:
            assignments = StudentAssignment.objects.filter(student=student, status='PENDING')
            if assignments.exists():
                text = f"📝 *{student.get_full_name() or student.username} Bekleyen Ödevler:*\n"
                for ast in assignments:
                    text += f"- {ast.assignment.title} (Son: {ast.assignment.deadline.strftime('%d.%m.%Y %H:%M')})\n"
                reply_parts.append(text)
            else:
                reply_parts.append(f"*{student.get_full_name() or student.username}* için bekleyen ödev yok. 🎉")
        return "\n".join(reply_parts)
        
    elif message_text == '4':
        for student in students:
            grades = Grade.objects.filter(student=student).exclude(grade__isnull=True)
            if grades.exists():
                text = f"📊 *{student.get_full_name() or student.username} Notlar:*\n"
                for g in grades:
                    text += f"- {g.exam.title}: {g.grade}\n"
                reply_parts.append(text)
            else:
                reply_parts.append(f"*{student.get_full_name() or student.username}* için girilmiş not bulunamadı.")
        return "\n".join(reply_parts)
        
    elif message_text == '5':
        for student in students:
            announcements = Announcement.objects.filter(classroom__students=student).order_by('-created_at')[:3]
            if announcements.exists():
                text = f"📢 *{student.get_full_name() or student.username} Son Duyurular:*\n"
                for ann in announcements:
                    text += f"- *{ann.title}*: {ann.content}\n"
                reply_parts.append(text)
            else:
                reply_parts.append(f"*{student.get_full_name() or student.username}* için duyuru bulunamadı.")
        return "\n".join(reply_parts)
        
    return MENU_TEXT

@csrf_exempt
def meta_webhook(request):
    if request.method == 'GET':
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        verify_token = os.getenv('WA_VERIFY_TOKEN')
        
        if mode == 'subscribe' and token == verify_token:
            logger.info("Webhook verified successfully.")
            return HttpResponse(challenge, status=200)
        else:
            logger.warning("Webhook verification failed.")
            return HttpResponse("Error, wrong validation token", status=403)
            
    elif request.method == 'POST':
        try:
            body = json.loads(request.body)
            
            if body.get('object') == 'whatsapp_business_account':
                for entry in body.get('entry', []):
                    for change in entry.get('changes', []):
                        value = change.get('value', {})
                        
                        if 'messages' in value:
                            for message in value['messages']:
                                sender_phone = message.get('from')
                                message_id = message.get('id')
                                
                                if message.get('type') == 'text':
                                    message_text = message.get('text', {}).get('body', '').strip()
                                    
                                    # Log INBOUND message
                                    WhatsAppMessageLog.objects.create(
                                        phone_number=sender_phone,
                                        direction='IN',
                                        message_type='MENU_QUERY',
                                        content=message_text
                                    )
                                    
                                    # Kullanıcıyı bul
                                    try:
                                        user = User.objects.get(phone_number=sender_phone)
                                    except User.DoesNotExist:
                                        send_whatsapp_message(
                                            sender_phone,
                                            "Numaranız sistemde kayıtlı değil. Lütfen mobil uygulamadan Profil > Telefon Numarası bölümünden kaydolun.",
                                            message_type='MENU_QUERY'
                                        )
                                        continue
                                        
                                    # Menü yanıtı oluştur ve gönder
                                    reply = build_reply(user, message_text)
                                    send_whatsapp_message(
                                        sender_phone,
                                        reply,
                                        recipient=user,
                                        message_type='MENU_QUERY'
                                    )
                                
                        if 'statuses' in value:
                            for status in value['statuses']:
                                message_id = status.get('id')
                                status_str = status.get('status')
                                # Direction kontrolü yapmıyoruz çünkü bizim OUT mesajlarımızın durumu güncelleniyor
                                # WhatsAppMessageLog.objects.filter(message_id=message_id).update(content=f"Durum: {status_str.upper()}") # Ya da status alanını ekleyebiliriz modelimize ama şu an yok.
                                logger.info(f"Message {message_id} status updated to {status_str}")
                                
            return HttpResponse("EVENT_RECEIVED", status=200)
            
        except json.JSONDecodeError:
            return HttpResponse("Invalid JSON", status=400)
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return HttpResponse("Error processing request", status=500)
            
    return HttpResponse("Method not allowed", status=405)
