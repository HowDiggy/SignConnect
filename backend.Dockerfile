# backend.Dockerfile

# Stage 1: Use a full Python image to build dependencies
FROM python:3.12 AS builder

# Set the working directory
WORKDIR /app

# Install system dependencies needed to build psycopg2 from source
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry

# Configure Poetry to create the virtualenv in the project's root directory
RUN poetry config virtualenvs.in-project true

# Copy dependency files and install them
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --without dev


# Stage 2: Create the final, slim production image
FROM python:3.12-slim

# Install the PostgreSQL runtime library (libpq5) and curl
# libpq5 is required by the compiled psycopg2 package from the builder stage.
# curl is required for the healthcheck in docker-compose.yml.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the pre-built virtual environment from the builder stage
COPY --from=builder /app/.venv ./.venv

# Copy the application source code
COPY ./src /app/src

# Make sure the application runs using the Python from our virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Using your original CMD as it is perfectly configured.
CMD ["uvicorn", "signconnect.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
