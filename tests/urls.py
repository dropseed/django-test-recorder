# -*- coding: utf-8
from __future__ import unicode_literals, absolute_import

from django.conf.urls import url, include

from test_recorder.urls import urlpatterns as test_recorder_urls

urlpatterns = [
    url(r'^', include(test_recorder_urls, namespace='test_recorder')),
]
