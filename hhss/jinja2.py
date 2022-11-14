from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse_lazy
from jinja2 import Environment
from django.contrib import messages
from django.utils import translation
from django.urls.base import resolve
from django.shortcuts import redirect


def change_lang(request, lang=None, *args, **kwargs):
    """
    Get active page's url by a specified language, it activates
    Usage: {{ change_lang(request, 'en') }}
    """

    path = request.path
    url_parts = resolve(path)

    url = path
    cur_language = translation.get_language()
    try:
        translation.activate(lang)
        url = reverse_lazy(url_parts.view_name, kwargs=url_parts.kwargs)
    finally:
        translation.activate(cur_language)

    return "%s" % url


def environment(**options):
    env = Environment(extensions=['jinja2.ext.i18n'], **options)
    env.install_gettext_translations(translation)
    env.globals.update({
        'get_messages': messages.get_messages,
        'static': staticfiles_storage.url,
        'url': reverse_lazy,
        'zip': zip,
        'list': list,
        'len': len,
        'get_language': translation.get_language,
    })
    return env
