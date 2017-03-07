# django-test-recorder [![Build Status](https://travis-ci.org/dropseedlabs/django-test-recorder.svg?branch=master)](https://travis-ci.org/dropseedlabs/django-test-recorder) [![codecov](https://codecov.io/gh/dropseedlabs/django-test-recorder/branch/master/graph/badge.svg)](https://codecov.io/gh/dropseedlabs/django-test-recorder)


Middleware and test classes for capturing and replaying HTTP-based tests. Utilizes [VCR.py](https://github.com/kevin1024/vcrpy) to record and play back HTTP requests that flow through your Django project.

1. Enable the middleware to capture incoming and outgoing requests
  ```python
  MIDDLEWARE = [
      # ... the rest of your middleware 
      'recorder.middleware.RecorderMiddleware',
  ]
  ```

1. Decide where recordings should be saved
  ```python
  from test_recorder.utils import set_cassettes_path

  set_cassettes_path('/app/webhooks/tests/cassettes')
  ```

  // TODO should also be able to set in settings.py or somewhere easier?

1. Set a recording name (optional)
  Helps to identify what the recorded calls were for (i.e. an event like `issue_created`). Will be used in filename.
  ```python
  from test_recorder.utils import set_recording_name

  set_recording_name('issue_created')
  ```
  
1. Capture requests
  Any incoming django requests will be captured as `{index}_{name}_incoming.json` and any resulting request calls made while processing the response will be saved as `{index}_{name}_outgoing.json`. You can leave everything enabled, change the recording name, and continue to capture more sequential requests.
  
1. Disable middleware
  When you're done capturing those calls for your tests, disable the middleware so you don't continue to collect things you don't care about.
  
1. You can now write tests using your recordings
```python
from os import path

from django.core.cache import cache

from test_recorder.test import RecorderTestCase

from repos.models import Repo
from owners.models import Owner


CASSETTES_PATH = path.join(path.dirname(__file__), 'cassettes')


class IssueCreatedTests(RecorderTestCase):
    def setUp(self):
        self.recording_names = ['0_installation_created', '1_issue_created']
        self.cassettes_path = CASSETTES_PATH
        self.client_headers = ('HTTP_X_HUB_SIGNATURE', 'HTTP_X_GITHUB_EVENT')  # headers to pass to django test client from recordings
        super(IssueCreatedTests, self).setUp()

    def test_issue_create(self):
        self.assertEqual(Owner.objects.count(), 0)
        self.assertEqual(Repo.objects.count(), 0)

        # owner and repo need to exist first (had to be installed)
        self._use_recorder(0)  # play the installation
        request, outgoing_cassette = self.receive_incoming_request(expected_status_code=200)
        self.assertEqual(len(outgoing_cassette.requests), 7)
        self.assertTrue(outgoing_cassette.all_played)

        self.assertEqual(Owner.objects.count(), 1)
        self.assertEqual(Repo.objects.count(), 1)

        self._use_recorder(1)  # play the issue creation
        request, outgoing_cassette = self.receive_incoming_request(expected_status_code=200)
        self.assertEqual(len(outgoing_cassette.requests), 2)
        self.assertTrue(outgoing_cassette.all_played)

        self.assertEqual(Repo.objects.count(), 1)
        self.assertEqual(Owner.objects.count(), 1)

        repo = Repo.objects.first()
        self.assertEqual(repo.issues.count(), 1)
        self.assertEqual(repo.pull_requests.count(), 0)
```

---

The recording process can be easily scripted using a few helper classes. Makes it easy to re-record your tests so you can then test how your response to those events has changed.
```python
from test_recorder.utils import middleware_enabled, set_recording_name, set_cassettes_path

from repos.models import Repo


if not middleware_enabled():
    exit("Middleware be enabled")

set_cassettes_path('/app/webhooks/tests/cassettes')
set_recording_name('installation_created')
print('Go install the integration')
input('Hit a key when done all transactions for this event have been processed ')

repo = Repo.objects.get(full_name='dropseedlabs/workman-testing')
set_recording_name('issue_created')
repo.github_repo.create_issue('Test capture', 'This is the body')

print('All done, go disable the middleware')
```
