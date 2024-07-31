# your_app/templatetags/custom_filters.py
from django import template
from django.db.models.fields.related import ManyToManyField

register = template.Library()

@register.filter
def is_many_to_many(field):
    return isinstance(field.field, ManyToManyField)