from django import template
from django.utils.translation import gettext as _

register = template.Library()


@register.filter(name='translate_text')
def translate_text(value):
    """Translate runtime strings such as DB-backed notifications/messages."""
    if value is None:
        return ''
    return _(str(value))
