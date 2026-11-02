# CI/CD examples

The `deploy` commands block until the deployment has finished and exit non-zero on failure, so they can be used
directly as a pipeline step. Provide the credentials via environment variables from your CI secret store.

## GitHub Actions

```yaml
name: deploy
on:
  push:
    tags: ["v*"]

jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      API_BASE_URL: ${{ vars.MAWS_API_BASE_URL }}
      API_CLIENT_ID: ${{ secrets.MAWS_API_CLIENT_ID }}
      API_CLIENT_SECRET: ${{ secrets.MAWS_API_CLIENT_SECRET }}
      IMAGE: 123456789012.dkr.ecr.eu-central-1.amazonaws.com/my-app:${{ github.ref_name }}
    steps:
      - name: Install maws
        run: |
          sudo curl -Lo /usr/local/bin/maws https://github.com/skaylink/maws/releases/download/latest/maws_$(arch)
          sudo chmod +x /usr/local/bin/maws
      - name: Deploy service
        run: maws ecs services deploy my-service "$IMAGE"
      - name: Deploy scheduled task
        run: maws ecs tasks deploy nightly-report "$IMAGE" --schedule-expression 'cron(0 3 * * ? *)'
```

## GitLab CI

```yaml
deploy:
  stage: deploy
  image: python:3.12-slim
  variables:
    API_BASE_URL: "https://<your-deployment-endpoint>"
    # API_CLIENT_ID and API_CLIENT_SECRET are defined as masked CI/CD variables
  script:
    - pip install maws
    - maws ecs services deploy my-service "$CI_REGISTRY_IMAGE:$CI_COMMIT_TAG"
  rules:
    - if: $CI_COMMIT_TAG
```

## Deploy all services with the same image

```bash
for service in $(maws ecs services list); do
  maws ecs services deploy "$service" my-registry/my-app:1.2.3
done
```
