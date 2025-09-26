# TrueFoundry Email Automation - Docker Compose Commands
.PHONY: help build up down logs clean setup start stop restart status health

# Default target
help: ## Show this help message
	@echo "TrueFoundry Email Automation - Docker Compose Commands"
	@echo "========================================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Setup commands
setup: ## Initial setup - copy environment template
	@echo "Setting up environment..."
	@cp env.template .env
	@echo "✅ Created .env file from template"
	@echo "🔧 Please edit .env file with your configuration"

# Docker Compose commands
build: ## Build the Docker images
	@echo "Building Docker images..."
	docker-compose build

up: ## Start the application (with build)
	@echo "Starting TrueFoundry Email Automation..."
	docker-compose up --build

start: up ## Alias for 'up'

up-d: ## Start the application in background
	@echo "Starting TrueFoundry Email Automation in background..."
	docker-compose up --build -d

daemon: up-d ## Alias for 'up-d'

down: ## Stop and remove containers
	@echo "Stopping TrueFoundry Email Automation..."
	docker-compose down

stop: down ## Alias for 'down'

restart: ## Restart the application
	@echo "Restarting TrueFoundry Email Automation..."
	docker-compose down
	docker-compose up --build -d

# Monitoring commands
logs: ## Show application logs
	docker-compose logs -f email-automation

status: ## Show container status
	@echo "Container Status:"
	@docker-compose ps

health: ## Check application health
	@echo "Checking application health..."
	@curl -s http://localhost:8080/health | jq '.' || echo "❌ Application not responding or jq not installed"

# Maintenance commands
clean: ## Clean up containers, images, and volumes
	@echo "Cleaning up Docker resources..."
	docker-compose down -v --remove-orphans
	docker system prune -f
	docker volume prune -f

reset: clean setup ## Full reset - clean and setup from scratch

# Development commands
shell: ## Open shell in running container
	docker-compose exec email-automation /bin/bash

dev-logs: ## Show detailed logs for development
	docker-compose logs -f --tail=100 email-automation

# Quick access commands
web: ## Open web browser to application
	@echo "Opening application in browser..."
	@which open > /dev/null 2>&1 && open http://localhost:8080 || echo "Please open http://localhost:8080 in your browser"

api: ## Open API documentation
	@echo "Opening API documentation in browser..."
	@which open > /dev/null 2>&1 && open http://localhost:8080/docs || echo "Please open http://localhost:8080/docs in your browser"

# Testing commands
test-upload: ## Test with sample CSV upload (requires running application)
	@echo "Testing sample CSV upload..."
	@curl -X POST "http://localhost:8080/api/validate" \
		-H "accept: application/json" \
		-H "Content-Type: multipart/form-data" \
		-F "file=@sample_prospects.csv" | jq '.' || echo "❌ Test failed or jq not installed"

# Information commands
info: ## Show application URLs and status
	@echo "TrueFoundry Email Automation Information"
	@echo "======================================="
	@echo "🌐 Main Application: http://localhost:8080"
	@echo "🎨 Streamlit Frontend: http://localhost:8501"  
	@echo "📖 API Documentation: http://localhost:8080/docs"
	@echo "🔧 Backend API: http://localhost:8080/api"
	@echo ""
	@echo "Container Status:"
	@docker-compose ps 2>/dev/null || echo "❌ Docker Compose not running"

# Environment commands
env-check: ## Check environment configuration
	@echo "Environment Configuration Check:"
	@echo "================================"
	@if [ -f .env ]; then \
		echo "✅ .env file exists"; \
		echo "📋 Environment variables:"; \
		grep -E '^[^#].*=' .env | head -5 || echo "No variables found"; \
	else \
		echo "❌ .env file not found. Run 'make setup' first"; \
	fi

# Network commands
network-info: ## Show Docker network information
	@echo "Docker Network Information:"
	@docker network ls | grep email-automation || echo "No email-automation networks found"

# Volume commands
volume-info: ## Show volume information
	@echo "Docker Volume Information:"
	@docker volume ls | grep email-automation || echo "No email-automation volumes found"
	@echo ""
	@echo "Output directory contents:"
	@ls -la output/ 2>/dev/null || echo "Output directory not found"

