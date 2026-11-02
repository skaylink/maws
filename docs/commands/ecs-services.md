# maws ecs services

Commands for long-running ECS services.

| Command                                   | Description                                 |
| ----------------------------------------- | ------------------------------------------- |
| [`deploy`](#maws-ecs-services-deploy)     | Deploy a new image to an ECS service        |
| [`status`](#maws-ecs-services-status)     | Get the status of an ECS service deployment |
| [`list`](#maws-ecs-services-list)         | List the available ECS services             |

## maws ecs services deploy

Deploys a new container image to an ECS service. After the deployment has been started, `maws` automatically
follows it like [`status`](#maws-ecs-services-status) does (polling every 5 seconds) and only returns once the
deployment succeeded or failed.

```text
maws ecs services deploy [OPTIONS] SERVICE_NAME IMAGE
```

### Arguments

| Argument       | Description                                    |
| -------------- | ---------------------------------------------- |
| `SERVICE_NAME` | Name of the service to update (required)       |
| `IMAGE`        | Container image to use for the service (required) |

### Options

| Option                  | Default      | Description                                                                                         |
| ----------------------- | ------------ | --------------------------------------------------------------------------------------------------- |
| `--force / --no-force`  | `--no-force` | Force a new deployment, even if the image has not changed                                           |
| `--secret-arns <arn>`   | –            | Secrets Manager secret ARN to attach to the service. Repeat the option to attach multiple secrets   |
| `--desired-count <n>`   | unchanged    | Desired number of running tasks (`>= 0`). If omitted, the current desired count is kept             |
| `--profile <name>`      | –            | Profile from `~/.skaylink/profile.toml`                                                             |

### Examples

Deploy a new image tag:

```bash
maws ecs services deploy my-service 123456789012.dkr.ecr.eu-central-1.amazonaws.com/my-app:1.2.3 --profile dev
```

```text
Deployment successfully started for service my-service
Checking deployment status for service my-service.......
Deployment succeeded with status 200.
```

Redeploy the same image, e.g. to pick up rotated secrets or restart all tasks:

```bash
maws ecs services deploy my-service 123456789012.dkr.ecr.eu-central-1.amazonaws.com/my-app:1.2.3 --force
```

Attach secrets to the service:

```bash
maws ecs services deploy my-service my-registry/my-app:1.2.3 \
  --secret-arns arn:aws:secretsmanager:eu-central-1:123456789012:secret:my-app/db-AbCdEf \
  --secret-arns arn:aws:secretsmanager:eu-central-1:123456789012:secret:my-app/api-key-GhIjKl
```

!!! note
    Secret ARNs must match `arn:aws:secretsmanager:<region>:<account-id>:secret:<name>`.

Scale the service while deploying:

```bash
maws ecs services deploy my-service my-registry/my-app:1.2.3 --desired-count 3
```

Scale a service down to zero tasks:

```bash
maws ecs services deploy my-service my-registry/my-app:1.2.3 --desired-count 0
```

## maws ecs services status

Polls the status of the current deployment of an ECS service and prints a dot for each check until the deployment is
finished. Exits with `0` when the deployment succeeded and `1` when it failed.

```text
maws ecs services status [OPTIONS] SERVICE_NAME
```

### Arguments

| Argument       | Description                                |
| -------------- | ------------------------------------------ |
| `SERVICE_NAME` | Name of the ECS service to check (required) |

### Options

| Option              | Default | Description                              |
| ------------------- | ------- | ---------------------------------------- |
| `--delay <seconds>` | `5`     | Seconds to wait between status checks    |
| `--profile <name>`  | –       | Profile from `~/.skaylink/profile.toml`  |

### Examples

Watch a running deployment:

```bash
maws ecs services status my-service --profile dev
```

```text
Checking deployment status for service my-service....
Deployment succeeded with status 200.
```

Check less frequently:

```bash
maws ecs services status my-service --delay 15
```

Failed deployment:

```text
Checking deployment status for service my-service...
Deployment failed with status 417.
```

## maws ecs services list

Prints the names of all ECS services you can deploy to, one per line.

```text
maws ecs services list [OPTIONS]
```

### Options

| Option             | Default | Description                             |
| ------------------ | ------- | --------------------------------------- |
| `--profile <name>` | –       | Profile from `~/.skaylink/profile.toml` |

### Examples

```bash
maws ecs services list --profile dev
```

```text
service-a
service-b
```

The output is plain text, so it can be piped into other tools:

```bash
maws ecs services list | grep frontend
```

If no services are available, `maws` prints `No ECS services available.`
