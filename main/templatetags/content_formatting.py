import re

from django import template
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import mark_safe


register = template.Library()
ACCENT_MARKER = re.compile(r"\*\*(.+?)\*\*")


@register.filter(needs_autoescape=True)
def accent_text(value, autoescape=True):
    """Render only **marked fragments** as a safe, branded emphasis."""
    source = str(value or "")
    escape = conditional_escape if autoescape else str
    rendered = []
    cursor = 0

    for match in ACCENT_MARKER.finditer(source):
        rendered.append(escape(source[cursor:match.start()]))
        rendered.append(format_html('<span class="content-accent">{}</span>', match.group(1)))
        cursor = match.end()

    rendered.append(escape(source[cursor:]))
    return mark_safe("".join(rendered))
