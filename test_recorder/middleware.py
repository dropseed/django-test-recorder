from .recorder import Recorder
from .utils import get_recording_name, get_cassettes_path


class RecorderMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response
        self.index = 0

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        recording_name = '{}_{}'.format(self.index, get_recording_name())
        self.recorder = Recorder(
                            recording_name=recording_name,
                            cassettes_path=get_cassettes_path(),
                            outgoing_record_mode='all'
                            )

        with self.recorder.use_outgoing_cassette():
            # process the response, recording all other request calls
            response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        self.recorder.save_incoming_request(request, response)

        self.index += 1  # increment the index for the next call

        return response
