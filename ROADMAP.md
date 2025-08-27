# SignConnect Project Roadmap

## Vision

The vision for SignConnect is to become a robust, go-to assistive communication tool for the deaf and non-verbal communities. It aims to be not just a functional application, but a reliable, scalable, and intuitive platform that seamlessly integrates into users' daily lives, making communication effortless and natural.

---

## Milestone 1: Core MVP & Production Readiness (Completed)

This phase focused on building the core application and hardening the backend to ensure it's stable, maintainable, and observable.

-   **[✓] Core Application**:
    -   Implemented real-time speech-to-text transcription.
    -   Developed AI-powered response suggestions using Google Gemini.
    -   Integrated `pgvector` for semantic matching of conversation context.
    -   Built a functional React frontend for user interaction.
    -   Secured the application with Firebase Authentication.
-   **[✓] Production-Ready Backend**:
    -   Containerized all services using Docker.
    -   Implemented structured logging with `structlog`.
    -   Integrated Sentry for real-time error monitoring and performance tracing.
    -   Established robust database migration management with **Alembic**.
-   **[✓] Architectural Improvements**:
    -   Refactored the WebSocket handling into a modular, testable service (`WebSocketManager`).
    -   Implemented a `src` layout and absolute imports for a cleaner, more maintainable Python backend.
-   **[✓] Automated CI/CD Pipeline**:
    -   Created a GitHub Actions workflow for automated testing.
    -   Automated the build and push of multi-architecture Docker images to GHCR.

---

## Milestone 2: Deployment & Operational Excellence (In Progress / Near-Term)

This phase is focused on deploying the application to a production environment and establishing best practices for monitoring and maintenance.

-   **[ ] Deployment to Kubernetes**:
    -   Create Kubernetes manifests (Deployment, Service, Ingress, etc.) for all services.
    -   Implement Kubernetes Secrets management for handling sensitive credentials.
    -   Set up a GitOps workflow using **ArgoCD** to automatically sync the cluster state with the Git repository.
-   **[ ] API Documentation**:
    -   Auto-generate and publish interactive API documentation using FastAPI's built-in OpenAPI/Swagger UI.
-   **[ ] Performance Benchmarking**:
    -   Establish baseline performance metrics (requests/second, latency).
    -   Conduct initial load testing to identify bottlenecks before public use.
-   **[ ] Enhanced User Feedback Mechanism**:
    -   Add a simple in-app feature for users to report bugs or suggest improvements, which could integrate with Sentry's feedback feature.

---

## Milestone 3: Feature Enhancement & Scalability (Mid-Term)

With the application stable in production, this phase will focus on enriching the user experience and ensuring the platform can handle growth.

-   **[ ] Advanced Personalization**:
    -   Allow the LLM to learn a user's unique communication style and vocabulary for even more personalized suggestions.
    -   Implement a user-facing dashboard to manage and fine-tune AI preferences.
-   **[ ] Multi-Language Support**:
    -   Expand the speech-to-text and response suggestion capabilities to support languages other than English.
-   **[ ] Monitoring & Observability Dashboards**:
    -   Create Grafana dashboards to visualize key application metrics (e.g., active users, API latency, error rates) for proactive monitoring.

---

## Long-Term Vision

These are ambitious, long-term goals that would significantly expand the impact and capabilities of SignConnect.

-   **[ ] Native Mobile Application**: Develop a dedicated iOS and Android application for a more integrated and accessible mobile experience.
-   **[ ] Offline Functionality**: Explore on-device models to provide transcription and basic response features even without an internet connection.
