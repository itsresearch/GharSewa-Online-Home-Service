from django import template

register = template.Library()

DAYS_OF_WEEK = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]

@register.filter
def day_numbers_to_names(day_numbers_str):
    if not day_numbers_str:
        return []
    try:
        numbers = [int(x) for x in day_numbers_str.split(',') if x.strip().isdigit()]
        return [DAYS_OF_WEEK[n] for n in numbers if 0 <= n < 7]
    except Exception:
        return [] 