# SignConnect


## Project Overview

SignConnect is an assistive technology web application designed to help deaf and non-verbal individuals navigate everyday conversations with ease. Using speech-to-text technology and AI-powered response suggestions, SignConnect creates a seamless bridge between spoken language and text-based communication.

### The Problem

For deaf and non-verbal individuals, spontaneous conversations can be challenging, especially in environments where:
- Communication partners don't know sign language
- Note-passing is impractical or too slow
- Professional interpreters aren't available

### Our Solution

SignConnect transforms spoken language into text in real-time and provides intelligent, contextual response suggestions based on the user's preferences and pre-configured scenarios.

## Key Features

- **Real-time Speech-to-Text**: Instantly convert spoken words into readable text
- **Context-Aware Response Suggestions**: Get personalized response options based on the conversation context
- **Scenario-Based Support**: Pre-configure responses for common situations like restaurants, medical appointments, or workplace meetings
- **User Preferences**: Store favorites, commonly used phrases, and personal details for quick access
- **Vector-Based Semantic Matching**: Understand the meaning behind questions for more accurate response suggestions

## Technology Stack

-   **Frontend**: React.js (built with Vite)
-   **Backend**: Python with FastAPI
-   **Database**: PostgreSQL with the `pgvector` extension for vector similarity search.
-   **Database Migrations**: **Alembic** for managing database schema changes.
-   **Speech Processing**: Google Cloud Speech-to-Text
-   **Vector Embeddings & AI**: Google Gemini
-   **Authentication**: Firebase Authentication
-   **Containerization**: Docker and Docker Compose
-   **CI/CD**: GitHub Actions
-   **Error Monitoring**: Sentry
-   **Deployment**: OCI Kubernetes

### **4. Project Structure (Monorepo)**

We are using a standard monorepo structure that cleanly separates the backend and frontend code.

```
SignConnect/
├── .github/                # CI/CD workflows
│   └── workflows/
│       └── ci.yml
├── frontend/               # All Frontend React code
│   ├── public/
│   └── src/
├── src/                    # All backend Python code
│   ├── alembic/            # Alembic migration scripts
│   │   └── versions/
│   └── signconnect/
│       ├── core/           # Core configurations and settings
│       ├── db/             # Database setup and ORM models
│       ├── llm/            # Large Language Model (LLM) interaction
│       ├── routers/        # FastAPI API route definitions
│       └── services/       # Business logic and service layer
├── tests/                  # All backend tests
│   ├── integration/
│   └── services/
├── .env.example            # Example environment variables
├── .gitignore
├── alembic.ini             # Alembic configuration
├── backend.Dockerfile
├── docker-compose.yml
├── poetry.lock
├── poetry.toml
├── pyproject.toml          # Python project and dependency definitions
├── README.md               # This file
└── ROADMAP.md              # Project vision and future plans
```

## Development Roadmap

SignConnect is being developed in phases:

- **Phase 1**: Foundation & Basic Functionality
- **Phase 2**: Intelligence & Personalization
- **Phase 3**: Advanced Features & Polish
- **Phase 4**: Portfolio Enhancement

*For detailed milestone information, see [ROADMAP.md](./ROADMAP.md)*


## Project Status

SignConnect is currently in early development. This project is being built as a portfolio piece to demonstrate full-stack development skills.

## Contributing

This project is currently a personal portfolio project and not open for contributions.

## Author

**Paulo Jauregui** - [LinkedIn](https://www.linkedin.com/in/paulo-jauregui/)

---

SignConnect: Bringing the conversation to everyone.
