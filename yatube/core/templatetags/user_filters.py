from django import template
from django.forms import Field


register = template.Library()


@register.filter
def addclass(field: Field, css: str) -> str:
    """Фильтр для добавления CSS-классов в теги."""
    return field.as_widget(attrs={'class': css})
