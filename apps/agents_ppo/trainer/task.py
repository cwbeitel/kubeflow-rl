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

from __future__ import absolute_import, division, print_function

import argparse
import datetime
import logging
import os
import pprint

import tensorflow as tf

import agents
import pybullet_envs  # To make AntBulletEnv-v0 available.

import pprint
import pip

flags = tf.app.flags

flags.DEFINE_string("run_mode", "train",
                    "Run mode, one of [train, render, train_and_render].")
flags.DEFINE_string("logdir", '/tmp/test',
                    "The base directory in which to write logs and "
                    "checkpoints.")
flags.DEFINE_string("hparam_set_id", "pybullet_kuka_ff",
                    "The name of the config object to be used to parameterize "
                    "the run.")
flags.DEFINE_string("run_base_tag",
                    datetime.datetime.now().strftime('%Y%m%dT%H%M%S'),
                    "Base tag to prepend to logs dir folder name. Defaults "
                    "to timestamp.")
flags.DEFINE_boolean("env_processes", True,
                     "Step environments in separate processes to circumvent "
                     "the GIL.")
flags.DEFINE_boolean("sync_replicas", False,
                     "Use the sync_replicas (synchronized replicas) mode, "
                     "wherein the parameter updates from workers are "
                     "aggregated before applied to avoid stale gradients.")
flags.DEFINE_integer("num_gpus", 0,
                     "Total number of gpus for each machine."
                     "If you don't use GPU, please set it to '0'")
flags.DEFINE_integer("save_checkpoint_secs", 600,
                     "Number of seconds between checkpoint save.")
flags.DEFINE_boolean("use_monitored_training_session", True,
                     "Whether to use tf.train.MonitoredTrainingSession to "
                     "manage the training session. If not, use "
                     "tf.train.Supervisor.")

flags.DEFINE_boolean("log_device_placement", False,
                     "Whether to output logs listing the devices on which "
                     "variables are placed.")
flags.DEFINE_boolean("debug", True,
                     "Run in debug mode.")
flags.DEFINE_boolean("dump_dependency_versions", False,
                     "Run in debug mode.")

# Render
flags.DEFINE_integer("render_secs", 600,
                     "Number of seconds between triggering render jobs.")
flags.DEFINE_string("render_out_dir", None,
                     "The path to which to copy generated renders.")
# TODO: Very not sure if this is correct way to do this. -------------
flags.DEFINE_string("fission_router_ip", "localhost",
                     "The ClusterIP of your Fission router service.")
# --------------------------------------------------------------------

# Algorithm
flags.DEFINE_string("algorithm", "agents.ppo.PPOAlgorithm",
                     "The name of the algorithm to use.")
flags.DEFINE_integer("num_agents", 30,
                     "The number of agents to use.")
flags.DEFINE_integer("eval_episodes", 25,
                     "The number of eval episodes to use.")
flags.DEFINE_string("env", "AntBulletEnv-v0",
                     "The gym / bullet simulation environment to use.")
flags.DEFINE_integer("max_length", 1000,
                     "The maximum length of an episode.")
flags.DEFINE_integer("steps", 10000000,
                     "The number of steps.")

# Network
flags.DEFINE_string("network", "agents.scripts.networks.feed_forward_gaussian",
                     "The registered network name to use for policy and value.")
# flags.DEFINE_string("policy_layers", "200,100",
#                      "A comma-separates list of the size of a series of layers "
#                      "to comprise the policy network.")
# flags.DEFINE_string("value_layers", "200,100",
#                      "A comma-separates list of the size of a series of layers "
#                      "to comprise the value network.")
flags.DEFINE_float("init_mean_factor", 0.1,
                     "unk")
flags.DEFINE_integer("init_logstd", -1,
                     "unk")

# Optimization
flags.DEFINE_float("learning_rate", 1e-4,
                     "The learning rate of the optimizer.")
flags.DEFINE_string("optimizer", "tensorflow.train.AdamOptimizer",
                     "The import path of the optimizer to use.")
flags.DEFINE_integer("update_epochs", 25,
                     "The number of update epochs.")
flags.DEFINE_integer("update_every", 30,
                     "The update frequency.")
# flags.DEFINE_boolean("optimizer_pre_initialize", True,
#                      "Whether to pre-initialize the optimizer.")

# Losses
flags.DEFINE_float("discount", 0.995,
                     "The discount.")
flags.DEFINE_float("kl_target", 1e-2,
                     "the KL target.")
flags.DEFINE_integer("kl_cutoff_factor", 2,
                     "The KL cutoff factor.")
flags.DEFINE_integer("kl_cutoff_coef", 1000,
                     "The KL cutoff coefficient.")
flags.DEFINE_integer("kl_init_penalty", 1,
                     "The initial KL penalty?.")

FLAGS = flags.FLAGS


def base_hparams_v1():
  # General
  algorithm = agents.ppo.PPOAlgorithm
  num_agents = 1
  eval_episodes = 25
  use_gpu = False

  # Environment
  env = 'KukaBulletEnv-v0'
  max_length = 1000
  steps = 10

  # Network
  network = agents.scripts.networks.feed_forward_gaussian
  weight_summaries = dict(
      all=r'.*',
      policy=r'.*/policy/.*',
      value=r'.*/value/.*')
  policy_layers = 200, 100
  value_layers = 200, 100
  init_mean_factor = 0.1
  init_logstd = -1

  # Optimization
  update_every = 30
  update_epochs = 25
  optimizer = tf.train.AdamOptimizer
  # optimizer_pre_initialize = True
  learning_rate = 1e-4

  # Losses
  discount = 0.995
  kl_target = 1e-2
  kl_cutoff_factor = 2
  kl_cutoff_coef = 1000
  kl_init_penalty = 1

  return locals()


def object_import_from_string(name):

    components = name.split('.')
    mod = __import__(components[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


def realize_import_attrs(d, filter):
    for k, v in d.items():
        if k in filter:
            # try:
            imported = object_import_from_string(v)
            # except ImportError as e:
            #     msg = ("Failed to realize import path %s." % v)
            #     raise e
            d[k] = imported
    return d


def _get_agents_configuration(hparam_set_name, log_dir=None, is_chief=False):
  """Load hyperparameter config."""
  try:
    # Try to resume training.
    hparams = agents.scripts.utility.load_config(log_dir)
  except IOError:

    hparams = base_hparams_v1()

    # --------
    # Experiment extending base hparams with FLAGS and dynamic import of
    # network and algorithm.
    for k, v in FLAGS.__dict__['__flags'].items():
        hparams[k] = v
    hparams = realize_import_attrs(hparams, ["network", "algorithm", "optimizer"])
    # --------

    hparams = agents.tools.AttrDict(hparams)

    if is_chief:
      # Write the hyperparameters for this run to a config YAML for posteriority
      hparams = agents.scripts.utility.save_config(hparams, log_dir)

  pprint.pprint(hparams)
  return hparams


def dump_dependency_versions():
  tf.logging.info("Tensorflow version: %s", tf.__version__)
  tf.logging.info("Tensorflow git version: %s", tf.__git_version__)

  import pip
  pprint.pprint(sorted(["%s==%s" % (i.key, i.version) for i in pip.get_installed_distributions()]))

  if FLAGS.run_mode == 'render':
      os.system("ffmpeg -version")


def upload_renders(render_dir, gcs_render_out_dir):

    from google.cloud import storage

    # Get a list of all files in the render_dir
    local_files = [f for f in os.listdir(render_dir) if os.path.isfile(os.path.join(render_dir, f))]
    print(local_files)

    storage_client = storage.Client()

    if not gcs_render_out_dir.startswith("gs://"):
        raise ValueError("upload_renders expected gcs_render_out_dir argument to start with gs://, saw %s" % gcs_render_out_dir)

    bucket_path = gcs_render_out_dir.split('/')[2]
    bucket = storage_client.get_bucket(bucket_path)

    blob_base_path = '/'.join(gcs_render_out_dir.split('/')[3:])
    print(blob_base_path)

    for local_filename in local_files:
        blob_path = os.path.join(blob_base_path, local_filename)
        blob = bucket.blob(blob_path)
        local_file_path = os.path.join(render_dir,local_filename)
        blob.upload_from_filename(local_file_path)


def main(unused_argv):
  """Run training.

  Raises:
    ValueError: If the arguments are invalid.
  """
  tf.logging.set_verbosity(tf.logging.INFO)

  if FLAGS.dump_dependency_versions:
      dump_dependency_versions()

  if FLAGS.debug:
    tf.logging.set_verbosity(tf.logging.DEBUG)

  run_config = tf.contrib.learn.RunConfig()

  log_dir = FLAGS.logdir

  agents_config = _get_agents_configuration(
      FLAGS.hparam_set_id, log_dir, run_config.is_chief)

  if FLAGS.run_mode == 'train':
    if run_config.is_chief:
      from .train import train
      for score in train(agents_config):
        tf.logging.info('Mean score: %s' % score)
      # for score in agents.scripts.train.train(agents_config, env_processes=True):
      #   logging.info('Score {}.'.format(score))
  if FLAGS.run_mode == 'render':
    render_tmp_dir = "/tmp/agents-render"
    os.system('mkdir %s' % render_tmp_dir)
    agents.scripts.visualize.visualize(
        logdir=FLAGS.logdir, outdir=render_tmp_dir, num_agents=1, num_episodes=1,
        checkpoint=None, env_processes=True)
    render_out_dir = FLAGS.render_out_dir
    if render_out_dir is None:
        render_out_dir = os.path.join(FLAGS.logdir, "render")
    upload_renders(render_tmp_dir, render_out_dir)


if __name__ == '__main__':
  tf.app.run()
