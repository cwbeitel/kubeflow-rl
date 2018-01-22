# Copyright 2017 The TensorFlow Agents Authors.
#
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

import tensorflow as tf

from tensorflow.python.training import basic_session_run_hooks
from tensorflow.python.training import session_run_hook
from tensorflow.python.training.summary_io import SummaryWriterCache
from tensorflow.python.training import training_util
from tensorflow.python.training.session_run_hook import SessionRunArgs
from tensorflow.core.framework.summary_pb2 import Summary


class RenderTriggerHook(session_run_hook.SessionRunHook):
  """Hook that counts steps per second."""

  def __init__(self,
               every_n_steps=None,
               every_n_secs=5,
               log_dir=None):

    if (every_n_steps is None) == (every_n_secs is None):
      raise ValueError(
          "exactly one of every_n_steps and every_n_secs should be provided.")
    self._timer = basic_session_run_hooks.SecondOrStepTimer(every_steps=every_n_steps,
                                    every_secs=every_n_secs)

    self._log_dir = log_dir
    self._render_count = 0
    self._total_elapsed_time = 0

  def begin(self):
    self._global_step_tensor = training_util._get_or_create_global_step_read()  # pylint: disable=protected-access
    if self._global_step_tensor is None:
      raise RuntimeError(
          "Global step should be created to use StepCounterHook.")

  def before_run(self, run_context):  # pylint: disable=unused-argument
    return SessionRunArgs(self._global_step_tensor)

  def after_run(self, run_context, run_values):
    _ = run_context

    stale_global_step = run_values.results
    if self._timer.should_trigger_for_step(stale_global_step+1):
      global_step = run_context.session.run(self._global_step_tensor)
      if self._timer.should_trigger_for_step(global_step):
        elapsed_time, elapsed_steps = self._timer.update_last_triggered_step(
            global_step)
        if elapsed_time is not None:
          self._total_elapsed_time += elapsed_time
          self._render_count += 1
          event_manifest = {"job_type": "render",
                            "args": {
                                "render_count": self._render_count,
                                "log_dir": self._log_dir,
                                "meta": {
                                    "elapsed_time": self._total_elapsed_time,
                                    "global_step": global_step
                                }
                            }}
          tf.logging.info("Triggering render number %s." % self._render_count)
          tf.logging.info("Render trigger manifest: %s" % event_manifest)
