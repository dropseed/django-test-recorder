from os import path

from django.conf import settings


RECORDING_NAME_FILE = path.join(path.dirname(__file__), 'meta', 'recording_name')
CASSETTES_PATH_FILE = path.join(path.dirname(__file__), 'meta', 'cassettes_path')


def middleware_enabled():
    return 'recorder.middleware.RecorderMiddleware' in settings.MIDDLEWARE


def _get_setting(file_path, default):
    if path.exists(file_path):
        return open(file_path, 'r').read()

    return default


def _set_setting(file_path, value):
    with open(file_path, 'w') as f:
        f.write(value)


def get_recording_name():
    return _get_setting(RECORDING_NAME_FILE, 'test')


def set_recording_name(value):
    _set_setting(RECORDING_NAME_FILE, value)


def get_cassettes_path():
    return _get_setting(CASSETTES_PATH_FILE, path.join(path.dirname(__file__), 'cassettes'))


def set_cassettes_path(value):
    _set_setting(CASSETTES_PATH_FILE, value)
