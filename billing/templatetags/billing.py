from django import template

register = template.Library()


@register.filter
def sum_by_field(object, field):
    return sum([obj.get(field) for obj in object])
