# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Use fission function to initiate an agents render job on kubernetes.

# Receives a message with a path to a logdir with new checkpoints to render.

# Creates and submits a custom render job referencing that log dir.

from flask import request
from flask import current_app
import os
import uuid
import json

from kubernetes import client, config

config.load_incluster_config()
v1 = client.BatchV1Api()

RENDER_IMAGE_TAG="gcr.io/kubeflow-rl/agents-ppo:cpu-7bd4bf03"


class RenderJobMessage(object):
    """Stores information related to a render job request or submission."""

    def __init__(self, from_json):
        """Initialize the render job message with a log_dir and job_type."""

        assert "job_type" in from_json
        assert "log_dir" in from_json
        assert from_json["job_type"] == "render"

        # TODO: Check log_dir is propperly formatted
        self.log_dir = from_json["log_dir"]
        self.job_type = from_json["job_type"]


def create_render_job(render_job_message):

    log_dir_name = render_job_message.log_dir.split('/')[-1]

    name = log_dir_name + "-render-" + str(uuid.uuid4())[0:8]
    job_manifest = {
        'kind': 'Job',
        'spec': {
            'template':
                {'spec':
                    {'containers': [
                        {'image': RENDER_IMAGE_TAG,
                         'name': name,
                         'args': ["--logdir", render_job_message.log_dir,
                                  "--run_mode=render"]
                         }],
                        'restartPolicy': 'Never'},
                    'metadata': {'name': name}}},
        'apiVersion': 'batch/v1',
        'metadata': {'name': name}}

    resp = v1.create_namespaced_job(
        body=job_manifest, namespace='rl')

    return resp


def main():
    headers = request.headers
    body = request.get_data()
    msg = "---HEADERS---\n%s\n--BODY--\n%s\n-----\n" % (headers, body)

    current_app.logger.info("Received request... %s" % msg)

    render_job = RenderJobMessage(from_json=request.get_json())
    job_data = create_render_job(render_job)
    # render_job.job_data = job_data
    # return json.dumps(render_job.__dict__)
    return str(job_data)
