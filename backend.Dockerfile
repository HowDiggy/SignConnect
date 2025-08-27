# backend.Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.12-slim

# install curl to perform health check for backend service
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Install poetry
RUN pip install poetry

# Configure Poetry to create the virtual environment inside the project directory (.venv).
RUN poetry config virtualenvs.in-project true

# Copy the dependency files to the working directory
COPY pyproject.toml poetry.lock ./

# Install project dependencies
RUN poetry install --no-root --without dev

# Copy the alembic configuration and migration scripts
COPY alembic.ini /app/
COPY src/alembic /app/alembic

# Copy the rest of the application's source code
COPY ./src /app/src
