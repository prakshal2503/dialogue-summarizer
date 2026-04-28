"""
Context processors for template globals.
"""
from .db import get_user_history


def sidebar_history(request):
    """Inject recent history into all templates for sidebar."""
    history = []
    if request.session.get('user_id') and request.session.get('user_role') != 'admin':
        try:
            history = get_user_history(request.session['user_id'], limit=6)
            # Convert _id to string for Django templates
            for item in history:
                item['id'] = str(item['_id'])
        except Exception:
            pass
    return {'sidebar_history': history}
