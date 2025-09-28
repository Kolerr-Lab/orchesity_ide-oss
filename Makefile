.PHONY: help install test format run clean

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

# Installation
install: ## Install dependencies
	pip install -r requirements.txt

# Testing
test: ## Run tests
	pytest tests/ -v

# Code Quality
format: ## Format code with black
	black src/ tests/

# Development
run: ## Run the application
	python -m src.main

# Cleanup
clean: ## Clean up cache files
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete