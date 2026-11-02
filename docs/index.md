# maws

`maws` is the Skaylink Managed AWS command line client. It talks to the Skaylink Managed AWS API to roll out new
container images to ECS services and ECS scheduled tasks, and to watch those deployments until they finish.

## Command overview

```text
maws
└── ecs                      ECS management commands
    ├── services             ECS service commands
    │   ├── deploy           Deploy a new image to an ECS service
    │   ├── status           Get the status of an ECS service deployment
    │   └── list             List the available ECS services
    └── tasks                ECS task commands
        ├── deploy           Deploy a new image to an ECS scheduled task
        ├── status           Get the status of an ECS scheduled task deployment
        └── list             List the available ECS tasks
```

See [Commands](commands/index.md) for a description of every subcommand including examples.

## Quick start

```bash
# 1. configure a profile (see "Configuration")
mkdir -p ~/.skaylink
cat > ~/.skaylink/profile.toml <<'EOF'
[profiles.dev]
API_BASE_URL = "https://<your-dev-deployment-endpoint>"
API_ACCESS_KEY = "<your-dev-api-token>"
EOF

# 2. find the service you want to deploy
maws ecs services list --profile dev

# 3. deploy a new image and wait for the rollout to finish
maws ecs services deploy my-service 123456789012.dkr.ecr.eu-central-1.amazonaws.com/my-app:1.2.3 --profile dev
```

## Requirements

- Skaylink Managed AWS infrastructure
- Skaylink Managed AWS API machine credentials (`API_CLIENT_ID` + `API_CLIENT_SECRET`) or a user token
  (`API_ACCESS_KEY`) with proper permissions
