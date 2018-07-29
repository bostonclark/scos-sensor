from __future__ import absolute_import

from actions import by_name # to get test mocks (see conftest.py)

from acquisitions.models import Acquisition
# includes models {schedule_entry, task_id, sigmf_metadata, data, created)

from django.conf import settings # used to get repo_root
from jsonschema import validate as schema_validate # used to validate sigmfm_metadata against
# scos_transfer_spec_schema.json

from schedule.tests.utils import post_schedule, TEST_SCHEDULE_ENTRY
# 

from sigmf.validate import validate as sigmf_validate
# a GNU radio file (sigmf) for validating sigmf

import json
import os


SCHEMA_FNAME = "scos_transfer_spec_schema.json"
SCHEMA_PATH = os.path.join(settings.REPO_ROOT, SCHEMA_FNAME)

with open(SCHEMA_PATH, "r") as f:
    schema = json.load(f)


def test_detector_time(user_client, rf):
    # Put an entry in the schedule that we can refer to
    rjson = post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    task_id = rjson['next_task_id']


    
    #assert(False)
    # use mock_acquire set up in conftest.py
    by_name['mock_time_acquire'](entry_name, task_id)
    acquistion = Acquisition.objects.get(task_id=task_id)
    sigmf_metadata = acquistion.sigmf_metadata
    assert sigmf_validate(sigmf_metadata)
    schema_validate(sigmf_metadata, schema)
