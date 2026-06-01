from django import template
from ..models import Category, User

register = template.Library()

# 1. Простой тег
@register.simple_tag
def site_name():
    return "Металлолом-Эксперт"

# 2. Тег с контекстными переменными
@register.simple_tag(takes_context=True)
def hello_user(context):
    request = context.get('request')
    if not request:
        return "Привет, Гость!"
    user_id = request.session.get('user_id')
    if user_id:
        try:
            my_user = User.objects.get(id=user_id)
            return f"Привет, {my_user.fio}!"
        except User.DoesNotExist:
            return "Привет, Гость!"
    return "Привет, Гость!"

# 3. Тег, возвращающий набор запросов (QuerySet)
@register.simple_tag
def get_all_categories():
    return Category.objects.all()