# rubber-duck

<img style="float:right" src="./actor.png" height="250" title="Miau"></img>

Microservice for ECS deployments

[![python](https://img.shields.io/badge/Python->=3.12-3776AB.svg?style=flat&logo=python&logoColor=white)][python-url]
[![typer](https://img.shields.io/badge/FastAPI-Typer-009688.svg?style=flat&logo=fastapi&logoColor=white)][typer-url]
[![uv](https://img.shields.io/badge/built%20with-uv-6c6cff?&logoColor=6c6cff&logo=python)][uv-url]
[![mise](https://img.shields.io/badge/using-mise-A8B1FF?logo=pnpm&logoColor=A8B1FF&style=flat)][mise-url]

[![pre-commit](https://github.com/skaylink/rubber-duck/actions/workflows/pre-commit.yml/badge.svg)](https://github.com/skaylink/rubber-duck/actions/workflows/pre-commit.yml)
[![tests](https://github.com/skaylink/rubber-duck/actions/workflows/tests.yml/badge.svg)](https://github.com/skaylink/rubber-duck/actions/workflows/tests.yml)

## Setup local development stack

### Install [mise][mise-url]

```bash
mise install
```

### Configuration

Create a `~/.skaylink/profile.toml` file with your API configurations:

```toml
[profiles.dev]
API_BASE_URL = "https://dev-api.example.com"
API_ACCESS_TOKEN = "your-dev-token"

[profiles.prod]
API_BASE_URL = "https://prod-api.example.com"
API_ACCESS_TOKEN = "your-prod-token"
```

#### Run the following command to execute the client locally

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
