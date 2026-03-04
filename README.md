# AI Agent Service

This repository contains a production-grade FastAPI service that implements an
AI planning and analysis agent. The service is cloud-agnostic and LLM-provider
agnostic; it can be invoked over HTTP from a .NET orchestrator or any other
client.

## Features

- **Planning Mode**: Receives an investigation query and tool registry, returns
  a structured execution plan in JSON.
- **Analysis Mode**: Accepts original query plus tool execution results, returns
  a structured analysis.
- Strict JSON schema validation with Pydantic v2 models.
- Retry logic for invalid LLM responses.
- Correlation ID support and structured logging.
- Environment-driven configuration and modular LLM client.

## Structure

```
ai-agent/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   ├── logging_config.py
│   ├── agents/
│   │   ├── planning_agent.py
│   │   └── analysis_agent.py
│   ├── llm/
│   │   └── llm_client.py
│   ├── models/
│   │   ├── plan_models.py
│   │   └── analysis_models.py
│   ├── validators/
│   │   ├── schema_validator.py
│   │   └── tool_validator.py
│   └── prompts/
│       ├── planning_prompt.txt
│       └── analysis_prompt.txt
├── requirements.txt
├── Dockerfile
└── README.md
```

## Running Locally

1. **Create a virtual environment** (Python 3.11+):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```
3. **Start the server**:
   ```powershell
   uvicorn app.main:app --reload
   ```
4. **Health check**:
   ```powershell
   curl http://localhost:8000/health
   ```
5. **Plan endpoint**:
   ```powershell
   curl -X POST http://localhost:8000/plan -H "Content-Type: application/json" \
     -d '{"userQuery":"example","toolRegistry":["tool1","tool2"]}'
   ```

## Docker

Build and run using Docker:

```bash
docker build -t ai-agent:latest .
docker run -p 8000:8000 ai-agent:latest
```

## Extending the LLM client

The `app/llm/llm_client.py` file defines an abstract `LLMClient`. Add new
implementations for OpenAI, Azure, or other providers and adjust
`dependencies.get_llm_client` accordingly.

## Configuration

Environment variables are read via `.env` using Pydantic's `BaseSettings`.

- `APP_NAME`: service name
- `LOG_LEVEL`: log verbosity
- `LLM_PROVIDER`: which LLM client to use (default `local`)

## Notes

This service is intended to be invoked by an orchestrator which supplies the
`toolRegistry` and gathers tool execution results; the agent does not execute
tools itself.  The design focuses on separation between planning, validation,
and analysis.
