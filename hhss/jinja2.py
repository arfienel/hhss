from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from jinja2 import Environment
from django.contrib import messages


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'get_messages': messages.get_messages,
        'static': staticfiles_storage.url,
        'url': reverse,
    })
    return env
