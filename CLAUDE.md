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

| Variable | Description |
|----------|-------------|
| `LLM` | LLM provider (`openai`) |
| `OPENAI_API_KEY` | OpenAI API key (stored in GitHub secrets) |
| `OPENAI_MODEL` | Model to use (`gpt-5-mini`) |
| `IMAGE_PROVIDER` | Image generation provider (`dall-e-3`) |
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
