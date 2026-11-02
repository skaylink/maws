# maws ecs tasks

Commands for ECS scheduled tasks, i.e. tasks triggered by a schedule (cron/rate) or an event pattern.

| Command                               | Description                                        |
| ------------------------------------- | -------------------------------------------------- |
| [`deploy`](#maws-ecs-tasks-deploy)    | Deploy a new image to an ECS scheduled task        |
| [`status`](#maws-ecs-tasks-status)    | Get the status of an ECS scheduled task deployment |
| [`list`](#maws-ecs-tasks-list)        | List the available ECS tasks                       |

## maws ecs tasks deploy

Deploys a new container image to an ECS scheduled task and optionally changes its schedule. After the deployment has
been started, `maws` automatically follows it like [`status`](#maws-ecs-tasks-status) does (polling every 5 seconds)
and only returns once the deployment succeeded or failed.

```text
maws ecs tasks deploy [OPTIONS] TASK_NAME IMAGE
```

### Arguments

| Argument    | Description                                     |
| ----------- | ----------------------------------------------- |
| `TASK_NAME` | Name of the scheduled task to update (required) |
| `IMAGE`     | Container image to use for the task (required)  |

### Options

| Option                         | Default      | Description                                                                 |
| ------------------------------ | ------------ | --------------------------------------------------------------------------- |
| `--schedule-expression <expr>` | unchanged    | New schedule, e.g. `cron(0 3 * * ? *)` or `rate(1 hour)`                    |
| `--force / --no-force`         | `--no-force` | Force a new deployment, even if the image has not changed                   |
| `--profile <name>`             | –            | Profile from `~/.skaylink/profile.toml`                                     |

Schedule expressions use the
[EventBridge schedule syntax](https://docs.aws.amazon.com/scheduler/latest/UserGuide/schedule-types.html):
`rate(<value> <unit>)` or `cron(<minutes> <hours> <day-of-month> <month> <day-of-week> <year>)`. Always quote the
expression in the shell.

### Examples

Deploy a new image tag:

```bash
maws ecs tasks deploy nightly-report 123456789012.dkr.ecr.eu-central-1.amazonaws.com/report:2.0.0 --profile dev
```

```text
Deployment successfully started for task nightly-report
Checking deployment status for task nightly-report...
Deployment succeeded with status 200.
```

Deploy and run the task every day at 03:00 UTC:

```bash
maws ecs tasks deploy nightly-report my-registry/report:2.0.0 --schedule-expression 'cron(0 3 * * ? *)'
```

Deploy and run the task every hour:

```bash
maws ecs tasks deploy cleanup my-registry/cleanup:1.4.0 --schedule-expression 'rate(1 hour)'
```

Redeploy the same image:

```bash
maws ecs tasks deploy nightly-report my-registry/report:2.0.0 --force
```

## maws ecs tasks status

Polls the status of the current deployment of an ECS scheduled task and prints a dot for each check until the
deployment is finished. Exits with `0` when the deployment succeeded and `1` when it failed.

```text
maws ecs tasks status [OPTIONS] TASK_NAME
```

### Arguments

| Argument    | Description                                       |
| ----------- | ------------------------------------------------- |
| `TASK_NAME` | Name of the ECS scheduled task to check (required) |

### Options

| Option              | Default | Description                              |
| ------------------- | ------- | ---------------------------------------- |
| `--delay <seconds>` | `5`     | Seconds to wait between status checks    |
| `--profile <name>`  | –       | Profile from `~/.skaylink/profile.toml`  |

### Examples

```bash
maws ecs tasks status nightly-report --profile dev
```

```text
Checking deployment status for task nightly-report..
Deployment succeeded with status 200.
```

```bash
maws ecs tasks status nightly-report --delay 30
```

## maws ecs tasks list

Prints the names of all ECS scheduled tasks you can deploy to, one per line.

```text
maws ecs tasks list [OPTIONS]
```

### Options

| Option             | Default | Description                             |
| ------------------ | ------- | --------------------------------------- |
| `--profile <name>` | –       | Profile from `~/.skaylink/profile.toml` |

### Examples

```bash
maws ecs tasks list --profile dev
```

```text
task-a
task-b
```

If no tasks are available, `maws` prints `No ECS tasks available.`
