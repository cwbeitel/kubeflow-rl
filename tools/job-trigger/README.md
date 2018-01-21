# Job trigger

There are various situations where you might want to be able to trigger a job or tf-job on Kubernetes by publishing to a message queue, e.g.

* Trigger multiple asynchronous renders of an in-progress RL agent training job, e.g.

```json
{
  "type": "render",
  "args": {
    "log_dir": "gs://path/to/logs"
  }
}
```

* Trigger a workflow run in response to the arrival of data that needs processing

```json
{
  "type": "etl-workflow",
  "args": {
    "workflow": "which-etl-workflow",
    "staged_data_dir": "gs://path/to/data",
    "args": "etl workflow args"
  }
}
```

This is similar but in contrast to having the message-publishing party submit jobs on kubernetes themselves. This approach has various benefits that outweigh the added complexity, including:

* Separation of permissions to publish events (e.g. a training job or data upload utility) and to submit new jobs.
* Simplifying the interface for potentially various codebases needing to perform the same task (e.g. render an RL agent).
