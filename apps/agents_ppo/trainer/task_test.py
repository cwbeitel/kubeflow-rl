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

import unittest
import tensorflow as tf
import agents
import sys
import os
import tempfile

from .task import main

FLAGS = tf.app.flags.FLAGS


class TestRun(unittest.TestCase):

    def test_non_distributed_runs(self):
      os.environ['TF_CONFIG'] = '{"cluster":{"master":["pybullet-kuka-ff-c2f81017-master-v3k7-0:2222"]},"task":{"type":"master","index":0},"environment":"cloud"}'
      tmp_logdir = tempfile.mkdtemp()
      sys.argv.extend(["--steps=10000",
                       "--sync_replicas=False",
                       "--num_agents=1",
                       "--logdir=%s" % tmp_logdir])
      tf.app.run()

      # TODO: Even when a run completes successfully this exits with a system
      # error.

    # TODO: This doesn't work - tests interact. Need to set directly on FLAGS
    # then app.run with local version of flags.
    # def test_distributed(self):
    #   sys.argv.extend(["--steps=10",
    #                    "--sync_replicas=True"])
    #   tf.app.run()


if __name__ == '__main__':
    unittest.main()
