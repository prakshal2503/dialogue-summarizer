from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # ── MongoDB init only ─────────────────────────────────────────────────
        try:
            from .db import init_db
            init_db()
        except Exception as e:
            print(f"[WARNING] Could not initialize MongoDB: {e}")
            print("Make sure MongoDB is running and MONGODB_URI is correct.")