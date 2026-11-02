# Commands

All commands follow the pattern `maws <group> <resource> <action> [ARGUMENTS] [OPTIONS]`. Running a command group
without a subcommand prints its help, and every command accepts `--help`.

```bash
maws --help
maws ecs --help
maws ecs services deploy --help
```

## maws

The root command.

| Option                 | Description                                         |
| ---------------------- | --------------------------------------------------- |
| `--install-completion` | Install shell completion for the current shell      |
| `--show-completion`    | Print the completion script for the current shell   |
| `--help`               | Show the help and exit                              |

## maws ecs

ECS management commands. Contains two resource groups:

- [`maws ecs services`](ecs-services.md) – long-running ECS services
- [`maws ecs tasks`](ecs-tasks.md) – ECS scheduled tasks (triggered by a schedule or an event pattern)

## Common option

| Option              | Description                                                                       |
| ------------------- | --------------------------------------------------------------------------------- |
| `--profile <name>`  | Profile from `~/.skaylink/profile.toml`. Without it, environment variables are used. See [Configuration](../configuration.md). |

## Exit codes

| Code | Meaning                                                                                      |
| ---- | -------------------------------------------------------------------------------------------- |
| `0`  | Success                                                                                      |
| `1`  | Deployment could not be started, deployment failed, or configuration/authentication error    |
| `2`  | Invalid usage, e.g. missing argument or invalid option value                                 |
| `78` | A [deprecated command](deprecations.md) was called                                           |
