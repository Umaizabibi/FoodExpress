from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument and return an integer"""
    try:
        return int(float(value) * float(arg))
    except (ValueError, TypeError):
        return value

@register.filter
def subtract(value, arg):
    """Subtract the argument from the value and return an integer"""
    try:
        return int(float(value) - float(arg))
    except (ValueError, TypeError):
        return value

@register.filter
def add(value, arg):
    """Add the argument to the value and return an integer"""
    try:
        return int(float(value) + float(arg))
    except (ValueError, TypeError):
        return value
