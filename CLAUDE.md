# Presenton - Project Documentation

## Overview

Presenton is an AI-powered presentation generation service. It uses OpenAI for content generation and provides a web interface for creating presentations.

## Architecture

- **Frontend**: Next.js application (port 3000)
- **Backend**: FastAPI application (port 8000)
- **Reverse Proxy**: Nginx (port 80)
- **Vector Search**: Chroma (for icon search)
- **LLM Runtime**: Ollama (optional, for local models)

## Azure Infrastructure

### Container App

- **Name**: `tubeonai-presenton`
- **Resource Group**: `TubeOnAI`
- **Location**: East US
- **URL**: https://slides.tubeonai.com
- **Azure URL**: https://tubeonai-presenton.redcoast-55bc18ba.eastus.azurecontainerapps.io

### Container Registry (ACR)

- **Name**: `tubeonaipresenton`
- **URL**: tubeonaipresenton.azurecr.io
- **Location**: East US

### PostgreSQL Database

- **Server**: `presenton-db`
- **Location**: East US 2
- **Tier**: Burstable B1ms (~$13/month)
- **Database**: `presenton`
- **Admin User**: `presenton_admin`
- **Host**: presenton-db.postgres.database.azure.com

### Blob Storage (Images)

- **Storage Account**: `presentonimages`
- **Container**: `images`
- **Location**: East US
- **Access**: Public blob access (images served directly via URL)
- **URL Pattern**: `https://presentonimages.blob.core.windows.net/images/{uuid}.{ext}`

## Environment Variables

### LLM Provider Configuration

| Variable | Description |
|----------|-------------|
| `LLM` | LLM provider: `openai`, `azure`, `anthropic`, `google`, `ollama`, or `custom` |
| `OPENAI_API_KEY` | OpenAI API key (stored in GitHub secrets) |
| `OPENAI_MODEL` | Model to use (`gpt-5-mini`) |
| `IMAGE_PROVIDER` | Image generation provider: `dall-e-3`, `azure-dall-e`, `azure-flux`, `pexels`, etc. |

### Azure OpenAI Configuration

When using `LLM=azure`, configure these environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | `350b41a4e7fe42a9bf3e6510a79912b3` |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | `https://tubeonai-east-us-2-new.openai.azure.com` |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Deployment name for the model | `gpt-5-mini`, `claude-sonnet-4-5`, `grok-3`, etc. |
| `AZURE_OPENAI_API_VERSION` | API version (optional) | `2025-01-01-preview` (default: `2024-08-01-preview`) |
| `AZURE_MODEL` | Model identifier | Same as deployment name |

**Supported Azure-hosted models:**
- **OpenAI models**: `gpt-4o`, `gpt-5-mini`, `gpt-4-turbo`, etc.
- **Anthropic Claude**: `claude-sonnet-4-5`, `claude-haiku-4-5`, `claude-opus-4-5`
- **xAI Grok**: `grok-3`, `grok-2`
- **DeepSeek**: `deepseek-v3`, `deepseek-chat`
- **DALL-E**: `dall-e-3`, `dall-e-2` (for image generation with `IMAGE_PROVIDER=azure-dall-e`)

The system automatically detects the model type and routes requests to the appropriate API format (Anthropic API for Claude, OpenAI-compatible API for others).

### Azure FLUX Image Generation Configuration

When using `IMAGE_PROVIDER=azure-flux`, configure these environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_FLUX_API_KEY` | Azure API key for FLUX deployment | `350b41a4e7fe42a9bf3e6510a79912b3` |
| `AZURE_FLUX_ENDPOINT` | Azure OpenAI endpoint URL | `https://TubeOnAI-East-US-2-NEW.openai.azure.com` |
| `AZURE_FLUX_DEPLOYMENT_NAME` | FLUX deployment name | `FLUX-1.1-pro` |
| `AZURE_FLUX_MODEL` | FLUX model identifier | `FLUX-1.1-pro` |
| `AZURE_FLUX_API_VERSION` | API version (optional) | `2024-02-15-preview` (default) |

**Azure FLUX Features:**
- High-quality image generation using FLUX-1.1-pro model
- Supports 1024x1024 image size
- Returns images in PNG format via base64 encoding
- Automatically uploads to Azure Blob Storage if configured
- Fallback to local file storage if blob storage not available

### Other Configuration

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (stored in GitHub secrets) |
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Blob Storage connection string for image persistence |
| `CAN_CHANGE_KEYS` | Allow runtime API key changes (`false`) |
| `DISABLE_ANONYMOUS_TRACKING` | Disable analytics (`true`) |
| `RESTRICT_TO_PRESENTATION_ONLY` | Restrict UI to only `/presentation` route (`true`/`false`, default: `false`) |

## GitHub Secrets

The following secrets are configured in the GitHub repository:

- `TUBEONAIPRESENTON_AZURE_CLIENT_ID` - Azure service principal client ID
- `TUBEONAIPRESENTON_AZURE_TENANT_ID` - Azure tenant ID
- `TUBEONAIPRESENTON_AZURE_SUBSCRIPTION_ID` - Azure subscription ID
- `TUBEONAIPRESENTON_REGISTRY_USERNAME` - ACR username
- `TUBEONAIPRESENTON_REGISTRY_PASSWORD` - ACR password
- `OPENAI_API_KEY` - OpenAI API key
- `DATABASE_URL` - PostgreSQL connection string
- `AZURE_STORAGE_CONNECTION_STRING` - Azure Blob Storage connection string

## Deployment

### Automatic Deployment

Pushes to the `main` branch trigger automatic deployment via GitHub Actions:
- Workflow: `.github/workflows/tubeonai-presenton-AutoDeployTrigger-*.yml`
- Builds Docker image and pushes to ACR
- Deploys to Azure Container Apps

### Manual Deployment

```bash
# Trigger manual deployment
gh workflow run "Trigger auto deployment for tubeonai-presenton"

# Check deployment status
az containerapp revision list --name tubeonai-presenton --resource-group TubeOnAI -o table
```

## Common Operations

### Check Container Logs

```bash
az containerapp logs show --name tubeonai-presenton --resource-group TubeOnAI --tail 100
```

### Check Revision Status

```bash
az containerapp revision list --name tubeonai-presenton --resource-group TubeOnAI -o table
```

### Update Environment Variables

```bash
az containerapp update \
  --name tubeonai-presenton \
  --resource-group TubeOnAI \
  --set-env-vars "VAR_NAME=value"
```

### Enable/Disable Route Restriction

To restrict access to only the `/presentation` route:

```bash
# Enable restriction (only /presentation accessible)
az containerapp update \
  --name tubeonai-presenton \
  --resource-group TubeOnAI \
  --set-env-vars "RESTRICT_TO_PRESENTATION_ONLY=true"

# Disable restriction (all routes accessible)
az containerapp update \
  --name tubeonai-presenton \
  --resource-group TubeOnAI \
  --set-env-vars "RESTRICT_TO_PRESENTATION_ONLY=false"
```

When enabled, all routes except `/presentation` will show a "Page Not Found" message.

### Scale Replicas

```bash
az containerapp update \
  --name tubeonai-presenton \
  --resource-group TubeOnAI \
  --min-replicas 1 \
  --max-replicas 3
```

### Check Database Connection

```bash
az postgres flexible-server show --name presenton-db --resource-group TubeOnAI
```

## Troubleshooting

### 502 Bad Gateway

1. Check if FastAPI is running:
   ```bash
   az containerapp logs show --name tubeonai-presenton --resource-group TubeOnAI --tail 50 | grep uvicorn
   ```

2. FastAPI takes ~2 minutes to start (downloads Chroma models on each cold start)

3. Check for database connection errors in logs

### Database Connection Issues

- Ensure `DATABASE_URL` uses URL-safe password (no `@`, `!`, or other special chars)
- Format: `postgresql+asyncpg://user:password@host/database?sslmode=require`
- PostgreSQL firewall allows Azure services

### Presentation Not Found Errors

- If using SQLite (no DATABASE_URL), enable sticky sessions:
  ```bash
  az containerapp ingress sticky-sessions set --name tubeonai-presenton --resource-group TubeOnAI --affinity sticky
  ```
- With PostgreSQL, this shouldn't happen

## Local Development

```bash
# Start all services
npm run dev

# Or run individually
cd servers/nextjs && npm run dev
cd servers/fastapi && uvicorn main:app --reload
```

## API Endpoints

- `POST /api/v1/ppt/presentation/create` - Create a new presentation
- `GET /api/v1/ppt/outlines/stream/{id}` - Stream outline generation (SSE)
- `GET /api/v1/ppt/presentation/{id}` - Get presentation by ID
