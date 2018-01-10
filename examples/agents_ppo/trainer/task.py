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

flags = tf.app.flags

flags.DEFINE_string("mode", "train",
                    "Run mode, one of [train, render, train_and_render].")
flags.DEFINE_string("logdir", None,
                    "The base directory in which to write logs and "
                    "checkpoints.")
flags.DEFINE_string("config", "pybullet_kuka",
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
flags.DEFINE_string("debug_ui_type", "curses",
                    "Command-line user interface type (curses | readline)")

# TODO: Consider making ksonnet the primary means of managing model
# parameterization which would involve exposing all of the params currently
# hard-coded below (in pybullet_kuka) as command-line args.
# flags.DEFINE_boolean("network", 'feed_forward_gaussian',
#                      "The registered network name to use for policy and value.")
# flags.DEFINE_boolean("policy_layers", "200,100",
#                      "A comma-separates list of the size of a series of layers "
#                      "to comprise the policy network.")
# flags.DEFINE_boolean("value_layers", "200,100",
#                      "A comma-separates list of the size of a series of layers "
#                      "to comprise the value network.")
# flags.DEFINE_boolean("num_agents", 10,
#                      "The number of agents to use.")
# flags.DEFINE_boolean("steps", 1e7,
#                      "The number of steps.")
# flags.DEFINE_boolean("discount", 0.995,
#                      "The discount.")
# flags.DEFINE_boolean("kl_target", 1e-2,
#                      "the KL target.")
# flags.DEFINE_boolean("kl_cutoff_factor", 2,
#                      "The KL cutoff factor.")
# flags.DEFINE_boolean("kl_cutoff_coef", 1000,
#                      "The KL cutoff coefficient.")

FLAGS = flags.FLAGS


def define_simulation_graph(batch_env, algo_cls, config, global_step):
  """Define the algortihm and environment interaction.

  Args:
    batch_env: In-graph environments object.
    algo_cls: Constructor of a batch algorithm.
    config: Configuration object for the algorithm.

  Returns:
    Object providing graph elements via attributes.
  """
  step = global_step

  # pylint: disable=unused-variable
  is_training = tf.placeholder(tf.bool, name='is_training')
  should_log = tf.placeholder(tf.bool, name='should_log')
  do_report = tf.placeholder(tf.bool, name='do_report')
  force_reset = tf.placeholder(tf.bool, name='force_reset')

  algo = algo_cls(batch_env, step, is_training, should_log, config)

  done, score, summary = agents.tools.simulate(
      batch_env, algo, should_log, force_reset)

  message = 'Graph contains {} trainable variables.'
  tf.logging.info(message.format(agents.tools.count_weights()))
  # pylint: enable=unused-variable
  return agents.tools.AttrDict(locals())


def train(agents_config, env_processes=True, log_dir=None):
  """Training and evaluation entry point yielding scores.

  Resolves some configuration attributes, creates environments, graph, and
  training loop. By default, assigns all operations to the CPU.

  Args:
    config: Object providing configurations via attributes.
    env_processes: Whether to step environments in separate processes.

  Yields:
    Evaluation scores.
  """

  FLAGS = tf.app.flags.FLAGS

  if log_dir is None and hasattr(FLAGS, 'logdir'):
    log_dir = FLAGS.logdir

  run_config = tf.contrib.learn.RunConfig()

  server = tf.train.Server(
      run_config.cluster_spec, job_name=run_config.task_type,
      task_index=run_config.task_id)

  tf.reset_default_graph()

  if agents_config.update_every % agents_config.num_agents:
    tf.logging.warn('Number of agents should divide episodes per update.')

  worker_device = "/job:%s/replica:0/task:%d" % (run_config.task_type,
                                                 run_config.task_id)

  with tf.device(worker_device):

    # Use replica_device_setter in part so that if we are running without any
    # parameter servers the default is to store the global_step on the
    # worker_device.
    with tf.device(
        tf.train.replica_device_setter(
            worker_device=worker_device,
            cluster=run_config.cluster_spec)):
      global_step = tf.Variable(0, False, dtype=tf.int32, name='global_step')

    batch_env = agents.scripts.utility.define_batch_env(
        lambda: agents.scripts.train._create_environment(agents_config),
        agents_config.num_agents, env_processes)

    # Attempt to work around not fetchable ops when running synchronous
    # training, was not effective.
    optimizer = agents_config.optimizer(agents_config.learning_rate)

    if FLAGS.sync_replicas:
      optimizer = tf.train.SyncReplicasOptimizer(
          optimizer,
          replicas_to_aggregate=(
              run_config.num_worker_replicas),
          total_num_replicas=(run_config.num_worker_replicas)
      )
    with agents_config.unlocked:
      agents_config.optimizer = optimizer

    graph = define_simulation_graph(
        batch_env, agents_config.algorithm, agents_config, global_step)

    loop = agents.scripts.train._define_loop(
        graph, log_dir,
        agents_config.update_every * agents_config.max_length,
        agents_config.eval_episodes * agents_config.max_length)

    total_steps = int(
        agents_config.steps / agents_config.update_every *
        (agents_config.update_every + agents_config.eval_episodes))

    # Exclude episode related variables since the Python state of environments is
    # not checkpointed and thus new episodes start after resuming.
    saver = agents.scripts.utility.define_saver(exclude=(r'.*_temporary/.*',))

    sess_config = tf.ConfigProto(allow_soft_placement=True)
    if FLAGS.log_device_placement:
      sess_config.log_device_placement = True

    sess_config.gpu_options.allow_growth = True

    init_op = tf.global_variables_initializer()
    local_init_op = tf.local_variables_initializer()

    hooks = [tf.train.StopAtStepHook(last_step=total_steps)]

    if FLAGS.sync_replicas:
      opt = graph.algo._optimizer
      sync_replicas_hook = opt.make_session_run_hook(run_config.is_chief)
      hooks.append(sync_replicas_hook)

    scaffold = tf.train.Scaffold(
        saver=saver,
        init_op=init_op,
        local_init_op=local_init_op
    )

    with tf.train.MonitoredTrainingSession(
            master=server.target,
            is_chief=run_config.is_chief,
            checkpoint_dir=log_dir,
            scaffold=scaffold,
            hooks=hooks,
            save_checkpoint_secs=FLAGS.save_checkpoint_secs,
            save_summaries_steps=None,
            save_summaries_secs=None,
            config=sess_config,
            stop_grace_period_secs=120,
            log_step_count_steps=3000) as sess:

      global_step = sess.run(loop._step)
      steps_made = 1

      while not sess.should_stop():

        phase, epoch, steps_in = loop._find_current_phase(global_step)
        phase_step = epoch * phase.steps + steps_in

        if steps_in % phase.steps < steps_made:
          message = '\n' + ('-' * 50) + '\n'
          message += 'Phase {} (phase step {}, global step {}).'
          tf.logging.info(message.format(phase.name, phase_step, global_step))

        phase.feed[loop._reset] = (steps_in < steps_made)

        phase.feed[loop._log] = (
            phase.writer and
            loop._is_every_steps(phase_step, phase.batch, phase.log_every))
        phase.feed[loop._report] = (
            loop._is_every_steps(phase_step, phase.batch, phase.report_every))

        summary, mean_score, global_step, steps_made = sess.run(
            phase.op, phase.feed)

        if loop._is_every_steps(phase_step, phase.batch, phase.checkpoint_every) and run_config.is_chief:
          loop._store_checkpoint(sess, saver, global_step)

        if loop._is_every_steps(phase_step, phase.batch, phase.report_every):
          yield mean_score

        # TODO: Potentially integrate summary writing with
        # MonitoredTrainingSession.
        if summary and phase.writer and run_config.is_chief:
          # We want smaller phases to catch up at the beginnig of each epoch so
          # that their graphs are aligned.
          longest_phase = max(phase.steps for phase in loop._phases)
          summary_step = epoch * longest_phase + steps_in
          phase.writer.add_summary(summary, summary_step)

    batch_env.close()


def _get_agents_configuration(hparam_set_name, log_dir, is_chief=False):
  """Load hyperparameter config."""
  try:
    # Try to resume training.
    hparams = agents.scripts.utility.load_config(log_dir)
  except IOError:
    from . import hparams
    registry = hparams.Registry()
    hparams = registry.get_hparams(hparam_set_name)
    if is_chief:
      # Write the hyperparameters for this run to a config YAML for posteriority
      hparams = agents.scripts.utility.save_config(hparams, log_dir)
  return hparams


def main(unused_argv):
  """Run training.

  Raises:
    ValueError: If the arguments are invalid.
  """
  tf.logging.set_verbosity(tf.logging.INFO)
  tf.logging.info("Tensorflow version: %s", tf.__version__)
  tf.logging.info("Tensorflow git version: %s", tf.__git_version__)

  if FLAGS.debug:
    tf.logging.set_verbosity(tf.logging.DEBUG)

  run_config = tf.contrib.learn.RunConfig()

  FLAGS.logdir = os.path.join(
    FLAGS.logdir, '{}-{}'.format(FLAGS.run_base_tag, FLAGS.config))

  agents_config = _get_agents_configuration(
      FLAGS.config, FLAGS.logdir, run_config.is_chief)

  if (FLAGS.mode == 'train' or FLAGS.mode == 'train_and_render'):
    # for score in train(agents_config):
    #   tf.logging.info('Mean score: %s' % score)
    if run_config.is_chief:
      for score in agents.scripts.train.train(agents_config, env_processes=True):
        logging.info('Score {}.'.format(score))
  if (FLAGS.mode == 'render' or FLAGS.mode == 'train_and_render'):
    agents.scripts.visualize.visualize(
        logdir=FLAGS.logdir, outdir=FLAGS.logdir, num_agents=1, num_episodes=5,
        checkpoint=None, env_processes=True)
  if FLAGS.mode not in ['train', 'render', 'train_and_render']:
    raise ValueError('Unrecognized mode, please set the run mode with --mode '
                     'to train, render, or train_and_render.')


if __name__ == '__main__':
  tf.app.run()
