# rubber-duck

<img style="float:right" src="./actor.png" height="250" title="kermit"></img>

Microservice for ECS deployments

[![python](https://img.shields.io/badge/Python->=3.12-3776AB.svg?style=flat&logo=python&logoColor=white)][python-url]
[![typer](https://img.shields.io/badge/FastAPI-Typer-009688.svg?style=flat&logo=fastapi&logoColor=white)][typer-url]
[![uv](https://img.shields.io/badge/built%20with-uv-6c6cff?&logoColor=6c6cff&logo=python)][uv-url]
[![mise](https://img.shields.io/badge/using-mise-A8B1FF?logo=pnpm&logoColor=A8B1FF&style=flat)][mise-url]

## Setup local development stack

### Install [mise][mise-url]:

```
mise install
```

#### Run the following command to execute the client locally

```bash
mise dev ecs deploy
```

#### Run tests

```bash
mise test
```

### TODOs

- Add pytests
- Implement a basic logging
- Read envouirment variables (API_BASE_URL, API_ACCESS_TOKEN) - hardcoded in mise.toml from file (e.g. `.skaylink`)
- Publish application on pypi.org

<!-- links -->

[python-url]: https://www.python.org
[typer-url]: https://typer.tiangolo.com
[uv-url]: https://github.com/astral-sh/uv
[mise-url]: https://mise.jdx.dev/installing-mise.html#homebrew
