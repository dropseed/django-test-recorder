import json
from os import path

from django.conf import settings

from vcr import filters
from vcr.config import VCR
from vcr.request import Request
from vcr.cassette import Cassette
from vcr.serializers import jsonserializer


class Recorders(object):
    def __init__(self, recording_names, *args, **kwargs):
        self.recorders = [Recorder(name, *args, **kwargs) for name in recording_names]

    def __getitem__(self, index):
        return self.recorders[index]


class Recorder(object):
    def __init__(self, recording_name, cassettes_path, outgoing_record_mode='none'):
        self.recording_name = recording_name
        self.cassettes_path = cassettes_path

        self.incoming_cassette_path = self._get_cassette_path(recording_name + '_incoming')
        self.outgoing_cassette_path = self._get_cassette_path(recording_name + '_outgoing')

        self.serializer = jsonserializer
        self.serializer_str = 'json'

        self.outgoing_vcr = VCR(
            decode_compressed_response=True,
            serializer=self.serializer_str,
            record_mode=outgoing_record_mode,
            match_on=('method', 'port', 'query', 'uri')
            )

        if hasattr(settings, 'RECORDER_SETTINGS') and 'filter_headers' in settings.RECORDER_SETTINGS:
            self.filter_headers = settings.RECORDER_SETTINGS['filter_headers']
        else:
            self.filter_headers = []

    def _get_cassette_path(self, name):
        filename = '{}.json'.format(name)
        return path.join(self.cassettes_path, filename)

    def _filter_headers(self, headers):
        """filter out any headers that aren't strings"""
        headers = {k: v for k, v in headers.items() if isinstance(v, str) and k not in self.filter_headers}
        return headers

    def _load_vcr_request_from_django_request(self, django_request):
        headers = self._filter_headers(django_request.META)
        vcr_request = Request(
                                django_request.method,
                                django_request.get_raw_uri(),
                                django_request.body,
                                headers
                                )
        return vcr_request

    def _load_vcr_response_from_django_response(self, django_response):
        return {
            "status": {
                "message": django_response.reason_phrase,
                "code": django_response.status_code,
            },
            "headers": self._filter_headers(django_response._headers),
            "body": {
                "string": django_response.content,
            }
        }

    def get_incoming_request(self):
        cassette = Cassette.load(path=self.incoming_cassette_path, serializer=self.serializer)
        assert len(cassette.requests) == 1, 'Incoming cassette should have 1 recording'
        return cassette.requests[0]

    def get_incoming_request_data(self):
        request = self.get_incoming_request()
        body = request.body

        if request.headers['CONTENT_TYPE'] == 'application/json':
            return json.loads(body)

        return body

    def save_incoming_request(self, django_request, django_response):
        """save each incoming request as its own cassette"""
        recorded_request = self._load_vcr_request_from_django_request(django_request)
        recorded_response = self._load_vcr_response_from_django_response(django_response)

        def before_record(r):
            # decode responses so they're readable
            return filters.decode_response(r)

        # TODO could still use vcr, just grab the cassette obj from it to manually
        # add request...could reuse settings easier that way (like decode response, serializer)
        cassette = Cassette(
                        self.incoming_cassette_path,
                        record_mode='all',
                        serializer=self.serializer,
                        before_record_response=before_record
                        )
        cassette.append(recorded_request, recorded_response)
        cassette._save()

    def use_outgoing_cassette(self, **kwargs):
        """
        Use as:
        `with recorder.use_outgoing_cassette() as cassette:`
        """
        return self.outgoing_vcr._use_cassette(path=self.outgoing_cassette_path, filter_headers=self.filter_headers, **kwargs)
