.PHONY: help dev-frontend dev-backend dev

help:
	@echo "Available commands:"
	@echo "  make dev-frontend    - Starts the frontend development server (Vite)"
	@echo "  make dev-backend     - Starts the backend development server (Uvicorn with reload)"
	@echo "  make dev             - Starts both frontend and backend development servers"

dev-frontend:
	@echo "Starting frontend development server..."
	@cd frontend && npm run dev

dev-backend:
	@echo "Starting backend development server on port 8000..."
	@cd backend && langgraph dev --port 8000

# Run frontend and backend concurrently
dev:
	@echo "Starting both frontend and backend development servers..."
	@make dev-frontend & make dev-backend

build-frontend:
	@echo "Building frontend..."
	@cd frontend && npm install && npm run build

build-backend:
	@echo "Building backend..."
	@cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -e .

build:
	@make build-frontend
	@make build-backend

serve-frontend:
	@echo "Serving frontend..."
	@cd frontend && npm run preview

serve-backend:
	@echo "Serving backend on port 8000..."
	@cd backend && . .venv/bin/activate && langgraph dev --port 8000

serve:
	@make serve-frontend & make serve-backend