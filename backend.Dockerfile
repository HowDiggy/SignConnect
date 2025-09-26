# backend.Dockerfile

# --- Build Stage ---
FROM python:3.12-slim as builder

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

# --- Final Stage ---
FROM python:3.12-slim

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv ./.venv
# Copy the application code from the builder stage
COPY --from=builder /app/src ./src
COPY --from=builder /app/alembic.ini ./
COPY --from=builder /app/alembic ./alembic

# Add the virtual environment to the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose the port the app runs on
EXPOSE 8000

# The command to run when the container starts
CMD ["uvicorn", "signconnect.main:app", "--host", "0.0.0.0", "--port", "8000"]
