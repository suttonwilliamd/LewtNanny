"""
Makefile for LewtNanny development tasks
"""

.PHONY: help install install-dev test test-ui lint format clean run run-debug run-tkinter

# Default target
help:
	@echo "LewtNanny Development Tasks"
	@echo ""
	@echo "Installation:"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test         Run all tests"
	@echo "  test-ui      Run UI-specific tests"
	@echo "  test-unit    Run unit tests only"
	@echo "  test-cov     Run tests with coverage"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint         Run linting (flake8, mypy)"
	@echo "  format       Format code (black, isort)"
	@echo "  clean        Clean temporary files"
	@echo ""
	@echo "Running:"
	@echo "  run          Run application with defaults"
	@echo "  run-debug    Run with debug mode"
	@echo "  run-tkinter  Run with Tkinter UI"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-test.txt

# Testing
test:
	pytest

test-ui:
	pytest -m ui

test-unit:
	pytest -m "not ui and not integration"

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term

# Code quality
lint:
	flake8 src tests
	mypy src --ignore-missing-imports

format:
	black src tests
	isort src tests

format-check:
	black --check src tests
	isort --check-only src tests

# Cleaning
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# Running application
run:
	python main.py

run-debug:
	python main.py --debug --verbose

run-tkinter:
	python main.py --ui tkinter

run-no-ocr:
	python main.py --no-ocr

run-small:
	python main.py --window 800x600

# Development shortcuts
dev-test: install-dev test lint
dev-setup: install-dev format lint test