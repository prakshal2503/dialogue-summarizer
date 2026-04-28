from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # ── MongoDB init ──────────────────────────────────────────────────────
        try:
            from .db import init_db
            init_db()
        except Exception as e:
            print(f"[WARNING] Could not initialize MongoDB: {e}")
            print("Make sure MongoDB is running and MONGODB_URI is correct.")

        # ── Text T5 model ─────────────────────────────────────────────────────
        try:
            from .summarizer import load_model
            load_model()
        except Exception as e:
            print(f"[WARNING] Could not load text T5 model: {e}")

        # ── Audio model (Whisper + T5) ────────────────────────────────────────
        try:
            from .audio_processor import load_model as load_audio
            load_audio()
        except Exception as e:
            print(f"[WARNING] Could not load audio model: {e}")
            print("Place model files in 'audio_summarizer_model/' next to manage.py.")

        # ── Video model (FFmpeg + Whisper + T5) ───────────────────────────────
        try:
            from .video_processor import load_model as load_video
            load_video()
        except Exception as e:
            print(f"[WARNING] Could not load video model: {e}")
            print("Place model files in 'video_summarizer_model/' next to manage.py.")
