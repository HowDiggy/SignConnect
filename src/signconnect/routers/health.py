# src/signconnect/routers/health.py

from fastapi import APIRouter, status

# Best practice: create a dedicated router for health checks.
router = APIRouter(
    tags=["Health"],
)


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Simple health check endpoint for Kubernetes liveness and readiness probes.

    Pre-conditions:
    - The application server (Uvicorn) is running.

    Post-conditions:
    - Returns a JSON response with a 200 OK status code.
    - The response body contains {"status": "ok"}.
    """
    return {"status": "ok"}
