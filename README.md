# SignConnect

<div align="center">
  <h3>Breaking Communication Barriers</h3>
</div>

## Project Overview

SignConnect is an assistive technology web application designed to help deaf and non-verbal individuals navigate everyday conversations with ease. Using speech-to-text technology and AI-powered response suggestions, SignConnect creates a seamless bridge between spoken language and text-based communication.

### The Problem

For deaf and non-verbal individuals, spontaneous conversations can be challenging, especially in environments where:
- Communication partners don't know sign language
- Note-passing is impractical or too slow
- Professional interpreters aren't available

### Our Solution

SignConnect transforms spoken language into text in real-time and provides intelligent, contextual response suggestions based on the user's preferences and conversation history.

## Key Features

- **Real-time Speech-to-Text**: Instantly convert spoken words into readable text
- **Context-Aware Response Suggestions**: Get personalized response options based on the conversation context
- **Scenario-Based Support**: Pre-configure responses for common situations like restaurants, medical appointments, or workplace meetings
- **User Preferences**: Store favorites, commonly used phrases, and personal details for quick access
- **Vector-Based Semantic Matching**: Understand the meaning behind questions for more accurate response suggestions

## Technology Stack

- **Frontend**: React.js (Progressive Web App)
- **Backend**: Python with FastAPI
- **Database**: PostgreSQL with pgvector extension for semantic search
- **Speech Processing**: Google Cloud Speech-to-Text
- **Vector Embeddings**: Google Gemini
- **Deployment**: AWS/GCP/Azure/OCI (TBD)

### **4. Project Structure (Monorepo)**

We are using a standard monorepo structure that cleanly separates the backend and frontend code.

```
SignConnect/
├── .env                  # Backend environment variables (ignored)
├── .env.example          # Example environment variables
├── .gitignore            # Files and directories ignored by Git
├── backend.Dockerfile    # Dockerfile for the FastAPI backend service
├── docker-compose.yml    # Defines and configures all services (db, backend, frontend)
├── frontend.Dockerfile   # Dockerfile for the React frontend service
├── gcp-credentials.json  # Google Cloud service account key (ignored)
├── poetry.lock           # Exact versions of installed Python dependencies
├── poetry.toml           # Poetry virtual environment configuration
├── pyproject.toml        # Python project and dependency definitions
├── README.md             # Main project overview and instructions
├── ROADMAP.md            # Project vision, status, and future plans
|
├── frontend/             # All Frontend React code
│   ├── .env.local        # Frontend environment variables (ignored)
│   ├── index.html        # The single HTML page for the React app
│   ├── package.json      # Frontend dependencies (npm)
│   ├── vite.config.js    # Vite build tool configuration
│   └── src/
│       ├── App.jsx       # Main application component and state manager
│       ├── main.jsx      # React application entry point
│       ├── firebaseConfig.js # Firebase client-side initialization
│       └── components/   # Reusable React UI components
│           ├── Auth/
│           ├── Controls/
│           ├── Suggestions/
│           └── TranscriptionDisplay/
|
├── src/                   # All backend Python code
│   └── signconnect/
│       ├── core/          # Core configurations and settings
│       │   └── config.py
│       ├── db/            # Database setup and ORM models
│       │   ├── database.py
│       │   ├── models.py
│       │   └── test_database.py
│       ├── llm/           # Large Language Model (LLM) interaction logic
│       │   └── client.py
│       ├── routers/       # FastAPI API route definitions
│       │   ├── firebase.py
│       │   ├── questions.py
│       │   ├── scenarios.py
│       │   ├── users.py
│       │   └── websockets.py
│       ├── __init__.py    # Python package indicator
│       ├── app_factory.py # FastAPI application factory
│       ├── crud.py        # CRUD operations for database models
│       ├── dependencies.py# FastAPI dependency injection functions
│       ├── firebase.py    # Firebase Admin SDK integration
│       ├── main.py        # Main FastAPI application entry point
│       └── schemas.py     # Pydantic data validation models
└── tests/                 # All test files (unit, integration, etc.)
    ├── integration/       # Integration tests (e.g., database interactions)
    │   └── test_vector_search.py
    ├── __init__.py        # Python package indicator for tests
    ├── conftest.py        # Pytest fixtures for tests
    ├── test_llm_client.py
    ├── test_preferences.py
    ├── test_questions.py
    ├── test_scenarios.py
    ├── test_users.py
    └── test_websockets.py
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

<div align="center">
  <i>SignConnect: Bringing the conversation to everyone.</i>
</div>
