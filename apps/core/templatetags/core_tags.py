from django import template

register = template.Library()


@register.filter
def initials(name: str) -> str:
    """'Ayesha Siddiqui' -> 'AS'. Works for any script; falls back to '?'."""
    parts = str(name).split()
    return "".join(part[0] for part in parts[:2]).upper() or "?"
