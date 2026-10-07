from django.apps import AppConfig


class WaBotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wa_bot'

    def ready(self):
        import wa_bot.signals
    verbose_name = 'WhatsApp Bot'
