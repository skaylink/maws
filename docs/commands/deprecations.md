# Deprecations

## `maws ecs deploy` and `maws ecs status`

Older versions of `maws` had `deploy` and `status` directly below `maws ecs`. These commands are deprecated and no
longer functional; use the separate [`services`](ecs-services.md) and [`tasks`](ecs-tasks.md) groups instead.
Calling them prints a migration hint and exits with code `78` (`EX_CONFIG`), so pipelines fail instead of silently
doing nothing.

| Deprecated command                    | Replacement                                                                 |
| ------------------------------------- | --------------------------------------------------------------------------- |
| `maws ecs deploy <name> <image> ...`  | `maws ecs services deploy <name> <image> ...` or `maws ecs tasks deploy <name> <image> ...` |
| `maws ecs status <name> ...`          | `maws ecs services status <name> ...` or `maws ecs tasks status <name> ...` |

### Example

```bash
maws ecs deploy my-service my-registry/my-app:1.2.3
```

```text
'maws ecs deploy' has been removed. Use one of:
  maws ecs services deploy <service-name> <image> [OPTIONS]
  maws ecs tasks deploy <task-name> <image> [OPTIONS]
Aborted.
```
