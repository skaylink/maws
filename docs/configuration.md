# Configuration

`maws` needs the API endpoint and credentials. They can be supplied either via a profile file or via environment
variables.

## Settings

| Key                 | Description                                                         |
| ------------------- | ------------------------------------------------------------------- |
| `API_BASE_URL`      | Endpoint of your Skaylink Managed AWS API deployment                |
| `API_ACCESS_KEY`    | Personal user token, sent as `x-api-key` header                     |
| `API_CLIENT_ID`     | Client ID of a non-personal machine client                          |
| `API_CLIENT_SECRET` | Client secret of a non-personal machine client                      |

Use either `API_ACCESS_KEY` **or** `API_CLIENT_ID` + `API_CLIENT_SECRET`. With machine credentials `maws` first
exchanges them for a bearer token at the `/token` endpoint.

!!! note
    If both a token and client credentials are configured, `maws` prints a warning and uses `API_ACCESS_KEY`.

## Profile file

Create `~/.skaylink/profile.toml` (on Windows `%USERPROFILE%\.skaylink\profile.toml`) with one section per profile:

```toml
[profiles.dev] # use a personalized user token
API_BASE_URL = "https://<your-dev-deployment-endpoint>"
API_ACCESS_KEY = "<your-dev-api-token>"

[profiles.prod] # use a non-personal machine client
API_BASE_URL = "https://<your-prod-deployment-endpoint>"
API_CLIENT_ID = "<your-prod-deployment-id>"
API_CLIENT_SECRET = "<your-prod-deployment-secret>"
```

Select a profile with `--profile` on any command that talks to the API:

```bash
maws ecs services list --profile prod
```

When `--profile` is given, the values are taken from the profile only; environment variables are ignored.
If the file does not exist, `maws` prints an example configuration and exits with code `1`. If the profile does not
exist, `maws` lists the available profiles and exits with code `1`.

!!! warning
    The profile file contains secrets. Restrict its permissions, e.g. `chmod 600 ~/.skaylink/profile.toml`.

## Environment variables

Without `--profile`, `maws` reads the settings from the environment. This is the recommended way in CI/CD pipelines.

```bash
# user token
export API_BASE_URL="https://<your-deployment-endpoint>"
export API_ACCESS_KEY="<your-api-token>"
maws ecs services list

# machine client, one-off
env API_BASE_URL="https://<your-deployment-endpoint>" \
    API_CLIENT_ID="<client-id>" \
    API_CLIENT_SECRET="<client-secret>" \
    maws ecs tasks list
```
