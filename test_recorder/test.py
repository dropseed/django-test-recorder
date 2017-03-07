from django.test import TestCase
from django.conf import settings

from .recorder import Recorder, Recorders
from .utils import middleware_enabled


class RecorderTestCase(TestCase):
    def setUp(self):
        # make sure the middleware isn't turned on
        # we don't need to rerecord stuff right now
        self.assertFalse(middleware_enabled())
        assert hasattr(self, 'recording_name') or hasattr(self, 'recording_names')

        if not hasattr(self, 'outgoing_record_mode'):
            # by default we won't record anything,
            # and will fail if try unrecorded call
            self.outgoing_record_mode = 'none'

        if hasattr(self, 'recording_name'):
            self.recorder = Recorder(
                                recording_name=self.recording_name,
                                cassettes_path=self.cassettes_path,
                                outgoing_record_mode=self.outgoing_record_mode
                                )

        if hasattr(self, 'recording_names'):
            self.recorders = Recorders(
                                self.recording_names,
                                cassettes_path=self.cassettes_path,
                                outgoing_record_mode=self.outgoing_record_mode
                                )

        if not hasattr(self, 'default_client_kwargs'):
            self.default_client_kwargs = {'follow': True, 'secure': True}

        if not hasattr(self, 'client_headers'):
            self.client_headers = []

    def _use_recorder(self, index):
        self.recorder = self.recorders[index]

    def receive_incoming_request(self, expected_status_code=200):
        incoming_request = self.recorder.get_incoming_request()

        content_type = incoming_request.headers['CONTENT_TYPE']

        # build a dictionary with the headers we want, will be pased to client
        incoming_headers = {key: incoming_request.headers[key] for key in self.client_headers}

        with self.recorder.use_outgoing_cassette() as cassette:
            req = self.client.generic(
                        incoming_request.method,
                        incoming_request.uri,
                        data=incoming_request.body,
                        content_type=content_type,
                        **self.default_client_kwargs,
                        **incoming_headers,
                        )

            self.assertEqual(req.status_code, expected_status_code)

            # self.assertTrue(cassette.all_played)

            return req, cassette
