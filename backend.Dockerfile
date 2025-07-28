# backend.Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.12-slim

# install curl to perform health check for backend service
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/get/lists/*

# Set the working directory inside the container
WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy the dependency files to the working directory
# This is done first to leverage Docker's layer caching
COPY pyproject.toml poetry.lock ./

# Install project dependencies
# --no-root is used because we are managing the app dependencies, not installing the app itself as a package
RUN poetry install --no-root --without dev

# Copy the rest of the application's source code
COPY ./src /app/src

# The command to run when the container starts.
# We use --host 0.0.0.0 to make the server accessible from outside the container.
CMD ["poetry", "run", "uvicorn", "signconnect.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]