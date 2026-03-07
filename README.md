# InvestiCore - AI Agent Service

InvestiCore is a production-grade FastAPI service that implements a two-stage
AI planning and analysis workflow. It is LLM-provider agnostic and can be
invoked over HTTP from orchestrators, CLI tools, or any other client.

## Features

- **Planning Endpoint** (`/plan`): Analyzes an investigation query and available
  tools, returns a structured execution plan with steps, dependencies, and
  confidence scores.
- **Analysis Endpoint** (`/analyze`): Processes tool execution results and
  generates root-cause analysis with evidence, confidence, and recommendations.
- **Robust Error Handling**: Automatic retry logic (3 attempts) for invalid LLM
  responses with self-correction feedback.
- **Correlation ID Support**: Request tracing across service boundaries via
  `X-Correlation-ID` headers for full observability.
- **Strict Schema Validation**: Pydantic v2 models ensure all requests and
  responses conform to expected structure.
- **Structured Logging**: Correlation IDs embedded in logs for request tracing.
- **LLM Provider Abstraction**: Abstract `LLMClient` interface supports Ollama,
  OpenAI, Azure, and other providers.

## Project Structure

```
InvestiCore/
├── app/
│   ├── main.py                 # FastAPI app, endpoints, middleware
│   ├── config.py               # Settings via Pydantic BaseSettings
│   ├── dependencies.py         # Dependency injection (agents, correlation ID)
│   ├── logging_config.py       # Structured logging setup
│   ├── agents/
│   │   ├── planning_agent.py   # PlanningAgent: generates execution plans
│   │   └── analysis_agent.py   # AnalysisAgent: analyzes tool results
│   ├── llm/
│   │   ├── llm_client.py       # Abstract LMClient interface
│   │   └── ollama_client.py    # Ollama implementation
│   ├── models/
│   │   ├── plan_models.py      # PlanningRequest, PlanningResponse, PlanStep
│   │   └── analysis_models.py  # AnalysisRequest, AnalysisResponse, ToolResultItem
│   ├── validators/
│   │   ├── schema_validator.py # Schema validation logic
│   │   └── tool_validator.py   # Tool registry validation
│   └── prompts/
│       ├── planning_prompt.txt # System prompt for planning agent
│       └── analysis_prompt.txt # System prompt for analysis agent
├── requirements.txt            # Python dependencies
├── config.py                   # Root-level configuration
├── Dockerfile                  # Docker image definition
└── README.md
```

## API Endpoints

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "provider": "local",
  "model": "llama2"
}
```

### `POST /plan`
Generate an execution plan for an investigation.

**Request:**
```json
{
  "userQuery": "What might be causing the database connection failures?",
  "toolRegistry": ["query_logs", "check_health", "analyze_metrics", "check_db"]
}
```

**Response:**
```json
{
  "planId": "550e8400-e29b-41d4-a716-446655440000",
  "steps": [
    {
      "stepNumber": 1,
      "toolName": "check_health",
      "arguments": {},
      "reasoning": "First check overall system health status",
      "dependsOn": []
    },
    {
      "stepNumber": 2,
      "toolName": "query_logs",
      "arguments": {"timeRange": "last_hour", "filter": "error"},
      "reasoning": "Examine recent errors in system logs",
      "dependsOn": [1]
    }
  ],
  "overallReasoning": "The plan start with a health check, then analyze logs and metrics sequentially",
  "estimatedComplexity": "medium",
  "confidence": 0.85
}
```

### `POST /analyze`
Analyze tool execution results and generate insights.

**Request:**
```json
{
  "userQuery": "What might be causing the database connection failures?",
  "toolResults": [
    {
      "toolName": "check_health",
      "status": "success",
      "output": {"db_connection": "FAILED", "api_status": "UP"},
      "errorMessage": null,
      "durationMs": 245
    },
    {
      "toolName": "query_logs",
      "status": "success",
      "output": {"errors": ["Connection timeout on db:5432", "Retry failed after 3 attempts"]},
      "errorMessage": null,
      "durationMs": 512
    }
  ]
}
```

**Response:**
```json
{
  "rootCause": "Database server is unreachable on port 5432, likely due to network connectivity or service unavailability",
  "evidence": [
    "Health check shows db_connection status: FAILED",
    "Logs contain multiple 'Connection timeout on db:5432' entries",
    "Retry mechanism exhausted after 3 attempts"
  ],
  "confidence": 0.92,
  "recommendedActions": [
    "Verify database service is running",
    "Check network connectivity to db:5432",
    "Review recent infrastructure changes",
    "Check database service logs for startup errors"
  ],
  "toolsUsed": ["check_health", "query_logs"],
  "analysisNotes": "High confidence in network/connectivity issue due to consistent timeout patterns"
}
```

## Running Locally

### Prerequisites
- Python 3.11 or higher
- Ollama running locally (or another LLM provider configured)

### Setup Steps

1. **Create a virtual environment**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Configure environment** (optional):
   Create a `.env` file in the project root:
   ```
   APP_NAME=InvestiCore
   LOG_LEVEL=INFO
   LLM_PROVIDER=local
   OLLAMA_MODEL=llama2
   ```

4. **Start the server**:
   ```powershell
   uvicorn app.main:app --reload
   ```
   The API will be available at `http://localhost:8000`
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

5. **Test the service**:
   ```powershell
   # Health check
   curl http://localhost:8000/health

   # Test planning endpoint
   curl -X POST http://localhost:8000/plan `
     -H "Content-Type: application/json" `
     -d '{
       "userQuery": "Test query",
       "toolRegistry": ["tool1", "tool2"]
     }'
   ```

### With Correlation ID Tracing

```powershell
curl -X POST http://localhost:8000/plan `
  -H "Content-Type: application/json" `
  -H "X-Correlation-ID: test-123" `
  -d '{
    "userQuery": "Test query",
    "toolRegistry": ["tool1", "tool2"]
  }'
```

## Docker

### Build Docker Image

```bash
docker build -t investicore:latest .
```

### Run with Docker

```bash
docker run -p 8000:8000 \
  -e LLM_PROVIDER=local \
  -e LOG_LEVEL=INFO \
  investicore:latest
```

## Extending the LLM Client

The `app/llm/llm_client.py` file defines an abstract `LLMClient` interface.
Current implementation:
- **Ollama** (`app/llm/ollama_client.py`): Local LLM provider

To add a new provider (e.g., OpenAI, Azure):
1. Create a new class inheriting from `LLMClient` in `app/llm/`
2. Implement the async `complete()` method
3. Update `app/dependencies.py` `get_llm_client()` to instantiate the new provider
   based on the `LLM_PROVIDER` environment variable

## Configuration

Environment variables are loaded from `.env` file or system environment using
Pydantic's `BaseSettings` (`app/config.py`).

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `AI Agent Service` | Application display name |
| `LOG_LEVEL` | `INFO` | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LLM_PROVIDER` | `local` | LLM provider implementation to use |
| `OLLAMA_MODEL` | `llama2` | Model name when using Ollama provider |

### Example `.env` File

```
APP_NAME=InvestiCore
LOG_LEVEL=DEBUG
LLM_PROVIDER=local
OLLAMA_MODEL=llama2
```

## Architecture & Design

### Key Design Principles

1. **Separation of Concerns**: Planning, validation, and analysis are separate
   agents. The orchestrator drives the workflow.
2. **Tool Agnostic**: The service does not execute tools—it plans their use
   and analyzes their results. The orchestrator is responsible for actual
   tool execution.
3. **Error Resilience**: Up to 3 retry attempts with self-correcting LLM
   feedback for invalid JSON or schema violations.
4. **Full Observability**: Correlation IDs propagate across all logs and
   response headers, enabling end-to-end request tracing.
5. **Type Safety**: Pydantic v2 ensures strict request/response validation
   with clear error messages.

### Workflow

1. **Client sends planning request** → `/plan` with `userQuery` and `toolRegistry`
2. **Planning Agent** generates ordered steps with dependencies and reasoning
3. **Orchestrator executes** the planned tools in order
4. **Client sends analysis request** → `/analyze` with original query and tool results
5. **Analysis Agent** generates root cause, evidence, confidence, and recommendations

### Retry Logic

Both agents implement 3-attempt retry logic:
- Attempt 1: Initial LLM call
- Attempt 2+: If JSON parsing or schema validation fails, feed error back to LLM
  for self-correction
- Final fallback: Raise `RuntimeError` with details of the last error

### Middleware

- **ExceptionMiddleware**: Catches unhandled exceptions and returns 500 response
- **Correlation ID Middleware**: Reads/generates `X-Correlation-ID` header,
  propagates through logs and response headers

## Error Handling

### HTTP Status Codes

- **200 OK**: Request succeeded, valid response returned
- **400 Bad Request**: Invalid request payload or validation error
- **500 Internal Server Error**: Unhandled exception or LLM failure after retries

### Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `Connection refused to Ollama` | Ollama not running | Start Ollama: `ollama serve` |
| `JSON decode error after retries` | Invalid LLM output format | Check model config, try different model |
| `Tool not in registry` | Referenced tool not in `toolRegistry` | Verify tool names match |
| `Validation error: confidence must be 0-1` | LLM returned invalid confidence | Retry request, check prompts |

## Logging

Logs are structured with JSON fields and include:
- `timestamp`: ISO 8601 format
- `correlation_id`: Request tracing ID
- `level`: INFO, WARNING, ERROR, DEBUG
- `message`: Log message
- Additional context fields depending on endpoint

Example:
```json
{
  "timestamp": "2024-03-07T15:30:45Z",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "level": "INFO",
  "message": "/plan request received",
  "query": "What might be causing the database connection failures?"
}
```

## Performance & Limits

- **Timeout**: No explicit timeout (depends on LLM provider)
- **Retries**: 3 attempts max per request
- **Request Size**: Limited by FastAPI defaults (~16 MB)
- **Response Size**: No limit imposed by InvestiCore

## Contributing

When modifying the service:
1. Update relevant Pydantic models in `app/models/`
2. Update agent logic in `app/agents/`
3. Modify prompts in `app/prompts/`
4. Test with both planning and analysis endpoints
5. Verify logging includes correlation ID
6. Test with correlation ID in request headers

## License

[Add your license information here]
