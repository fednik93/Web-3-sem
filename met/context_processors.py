from .models import User


def session_user(request):
    """Добавляет current_user в контекст каждого шаблона — берётся из сессии,
    не из Django auth (у проекта своя система авторизации)."""
    user_id = request.session.get('user_id')
    if not user_id:
        return {'current_user': None}
    try:
        current_user = User.objects.select_related('role_id').get(pk=user_id)
    except User.DoesNotExist:
        current_user = None
    return {'current_user': current_user}