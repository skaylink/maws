# maws - Skaylink Managed AWS command line client

Provides tools for Skaylink managed services.

[![python](https://img.shields.io/badge/Python->=3.12-3776AB.svg?style=flat&logo=python&logoColor=white)][python-url]
[![typer](https://img.shields.io/badge/FastAPI-Typer-009688.svg?style=flat&logo=fastapi&logoColor=white)][typer-url]
[![uv](https://img.shields.io/badge/built%20with-uv-6c6cff?&logoColor=6c6cff&logo=python)][uv-url]
[![mise](https://img.shields.io/badge/using-mise-A8B1FF?logo=pnpm&logoColor=A8B1FF&style=flat)][mise-url]

[![pre-commit](https://github.com/skaylink/maws/actions/workflows/pre-commit.yml/badge.svg)](https://github.com/skaylink/maws/actions/workflows/pre-commit.yml)
[![tests](https://github.com/skaylink/maws/actions/workflows/tests.yml/badge.svg)](https://github.com/skaylink/maws/actions/workflows/tests.yml)

## Requirements

- Skaylink Managed AWS infrastructure
- Skaylink Managed AWS API machine credentials (`API_CLIENT_ID` + `API_CLIENT_SECRET`) or user token (`API_ACCESS_KEY`) and proper permissions

## Installation

### Linux Binary

You can download the [latest release binaries](https://github.com/skaylink/maws/releases/latest]).

Example:

```bash
sudo curl -Lo /usr/local/bin/maws https://github.com/skaylink/maws/releases/download/latest/maws_$(arch)
sudo chmod +x /usr/local/bin/maws
```

### Windows EXE

You can download the [latest release exe](https://github.com/skaylink/maws/releases/latest]).

### Pip

You can install the package for Python directly via `pip`.

```bash
pip install maws
```

## Configuration

You can either use environment variables `API_BASE_URL` and `API_CLIENT_ID` + `API_CLIENT_SECRET` or `API_ACCESS_KEY` or create a `~/.skaylink/profile.toml` file with your API access details:

```toml
[profiles.dev] # use a personalized user token
API_BASE_URL = "<your-dev-deployment-endpoint>"
API_ACCESS_KEY = "<your-dev-api-token>"

[profiles.prod] # use a non-personal machine client
API_BASE_URL = "<your-prod-deployment-endpoint>"
API_CLIENT_ID = "<your-prod-deployment-id>"
API_CLIENT_SECRET = "<your-prod-deployment-secret>"
```

## Usage

### With profiles

```bash
maws ecs deploy <service-name> <image> --profile <some-profile>
```

### With environment variables

```bash
env API_BASE_URL=<your-deployment-endpoint> API_ACCESS_KEY=<your-api-token> maws ecs deploy <service-name> <image>
```

## Development

### Install [mise][mise-url]

```bash
mise install
```
### Run commands

```bash
# Using a specific profile
mise dev ecs deploy service-name image-tag --profile dev
```

#### Run tests

```bash
mise test
```

<!-- links -->

[python-url]: https://www.python.org
[typer-url]: https://typer.tiangolo.com
[uv-url]: https://github.com/astral-sh/uv
[mise-url]: https://mise.jdx.dev/installing-mise.html#homebrew
