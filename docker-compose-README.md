# Docker Compose Setup for TrueFoundry Email Automation

This Docker Compose configuration sets up the complete TrueFoundry Sales Email Automation application with both the FastAPI backend and Streamlit frontend in a unified service.

## Quick Start

1. **Copy the environment template:**
   ```bash
   cp env.template .env
   ```

2. **Edit the `.env` file** with your specific configuration (especially the API key if different)

3. **Build and start the application:**
   ```bash
   docker-compose up --build
   ```

4. **Access the application:**
   - **Main Application**: http://localhost:8080
   - **Streamlit Frontend**: http://localhost:8501
   - **API Documentation**: http://localhost:8080/docs
   - **Backend API**: http://localhost:8080/api

## Services

### email-automation
The main unified application service that includes:
- **FastAPI Backend** (port 8080): Handles API requests and processing
- **Streamlit Frontend** (port 8501): Web interface for uploading and managing prospects
- **Unified Management**: Single service that manages both components

## Environment Variables

The application can be configured using environment variables in the `.env` file:

### TrueFoundry API Configuration
- `TFY_API_KEY`: Your TrueFoundry API key
- `TFY_BASE_URL`: TrueFoundry base URL (default: https://llm-gateway.truefoundry.com)
- `TFY_REASONING_MODEL`: Model to use (default: openai-main/gpt-5)

### Processing Configuration
- `CHUNK_SIZE`: Number of prospects to process at once (default: 5)
- `MAX_RETRIES`: Maximum retry attempts (default: 3)
- `TIMEOUT_SECONDS`: LLM API call timeout in seconds (default: 300)

### Output Configuration
- `OUTPUT_DIR`: Directory for output files (default: output)

### Logging Configuration
- `LOG_LEVEL`: Logging level (default: INFO)
- `ENABLE_TFY_LOGGING`: Enable TrueFoundry logging (default: true)

## Volume Mounts

- `./output:/app/output`: Persists generated research and email files
- `./sample_prospects.csv:/app/sample_prospects.csv`: Sample data file
- `./*.csv:/app/data/`: Any CSV files in the current directory

## Common Commands

### Start the application
```bash
docker-compose up
```

### Start in background
```bash
docker-compose up -d
```

### Build and start (after code changes)
```bash
docker-compose up --build
```

### View logs
```bash
docker-compose logs -f email-automation
```

### Stop the application
```bash
docker-compose down
```

### Reset volumes (clear all data)
```bash
docker-compose down -v
```

## Health Checks

The application includes built-in health checks:
- **Container Health**: `curl http://localhost:8080/health`
- **Status Check**: Visit http://localhost:8080/health in your browser

## File Structure

```
email_v1/
├── docker-compose.yml          # Main compose configuration
├── Dockerfile.truefoundry      # Application Dockerfile
├── env.template                # Environment variables template
├── .env                        # Your environment variables (create from template)
├── unified_app.py              # Main unified application
├── streamlit_app.py            # Streamlit frontend
├── email_automation.py         # Processing pipeline
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── output/                     # Generated files (persisted)
└── *.csv                       # Your prospect data files
```

## Troubleshooting

### Application won't start
1. Check if ports 8080 and 8501 are available
2. Verify your `.env` file configuration
3. Check logs: `docker-compose logs email-automation`

### API key errors
1. Ensure `TFY_API_KEY` is correctly set in `.env`
2. Verify the API key is valid and not expired

### Processing fails
1. Check the CSV format (requires: person_name, company_name, linkedin_url)
2. Verify network connectivity for API calls
3. Check processing logs in the container

### Port conflicts
If you need to use different ports, modify the `docker-compose.yml`:
```yaml
ports:
  - "8090:8080"  # Change 8090 to your preferred port
  - "8502:8501"  # Change 8502 to your preferred port
```

## Optional: Redis Integration

The compose file includes a commented Redis service for session management and caching. To enable:

1. Uncomment the Redis service in `docker-compose.yml`
2. Uncomment the Redis volume
3. Update your application code to use Redis for session storage

## Production Deployment

For production deployment, consider:
1. Use Docker Swarm or Kubernetes instead of Docker Compose
2. Set up proper secrets management for API keys
3. Configure reverse proxy (nginx) for SSL termination
4. Set up log aggregation and monitoring
5. Use persistent volumes for data storage
6. Configure backup strategies for output data

## Support

For issues related to:
- **TrueFoundry API**: Contact TrueFoundry support
- **Application bugs**: Check the application logs
- **Docker issues**: Verify Docker and Docker Compose installation
