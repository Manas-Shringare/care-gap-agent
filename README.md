# PromptTrace

**Observability Toolkit for Amazon Bedrock applications**

> ⚠️ This project is under active development. Sections below marked
> _(coming soon)_ will be completed as implementation progresses.

## What is PromptTrace?

PromptTrace is a lightweight observability toolkit for applications built on
Amazon Bedrock. It captures request/response data, latency, metadata, and
human feedback for every LLM invocation — giving you visibility into how
your Bedrock-backed application behaves in practice.

This is an intentionally scoped MVP: the goal is a clean, deployable
foundation for LLM observability, not a full LLMOps platform. See
[docs/ROADMAP.md](docs/ROADMAP.md) for what's in and out of scope.

## Tech Stack

- **Python 3.12** + **FastAPI** — API layer
- **Amazon Bedrock** — LLM inference
- **Amazon DynamoDB** — observability data persistence
- **Docker** + **AWS App Runner** — containerized deployment
- **uv** — dependency and virtual environment management

## Architecture

_(coming soon — architecture diagram and overview)_

## AWS Services Used

_(coming soon)_

## API Endpoints

_(coming soon)_

## Local Development

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- AWS credentials configured locally (`aws configure`) with Bedrock and
  DynamoDB access, for phases that call AWS

### Setup

```bash
git clone https://github.com/Manas-Shringare/prompttrace.git
cd prompttrace

uv sync
source .venv/bin/activate

cp .env.example .env
```

### Run

```bash
uvicorn app.main:app --reload
```

Then verify it's running:

```bash
curl http://localhost:8000/health
```

## Deployment

_(coming soon — AWS App Runner deployment overview)_

## Engineering Decisions

_(coming soon — key design decisions and tradeoffs)_

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## License

MIT — see [LICENSE](LICENSE).