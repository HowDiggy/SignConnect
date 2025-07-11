
---

## Project Recap: SignConnect

### **1. The Vision & Core Mission**

- **Project Name:** SignConnect
    
- **Mission:** To build an assistive Progressive Web App (PWA) that empowers deaf and hard-of-hearing individuals by providing real-time, AI-powered communication support.
    
- **Core Loop:** The application listens to spoken language, transcribes it to text, and suggests relevant, personalized responses for the user.
    
- **End Goal:** A high-impact portfolio project demonstrating a wide range of modern software engineering skills, with the potential to become a real-world SaaS business.
    

### **2. Development Environment & Tools**

- **Backend Framework:** **Python** with **FastAPI** for creating a high-performance, asynchronous API.
    
- **Frontend Language:** **JavaScript**, along with HTML and CSS. The UI is currently built with vanilla JS, with the possibility of adopting a framework like React later.
    
- **Database:** **PostgreSQL** running in a **Docker** container. We are using the `ankane/pgvector` image to enable vector search capabilities.
    
- **Dependency Management:** **Poetry** for managing all Python packages and project dependencies in a `pyproject.toml` file.
    
- **Code Editor:** You are using an IDE like PyCharm or WebStorm, which provides helpful linting and debugging features.
    

### **3. Workflow & Methods**

- **Version Control:** We are using **Git** and pushing our code to a remote repository on **GitHub**.
    
- **Authentication:** We have pivoted to a professional, third-party authentication service, **Firebase Authentication**, to securely manage all user sign-up, login, and identity verification. We are using Firebase ID tokens (JWTs) to secure our backend.
    
- **API Testing:** We are using **Postman** to manually test our API endpoints as we build them, ensuring they work correctly before integrating them with the frontend.
    
- **Database Migrations:** For our current development phase, we are handling database schema changes by manually resetting the Docker volume. As the project matures, we would implement a formal migration tool like **Alembic**.
    

### **4. Project Structure (Monorepo)**

We are using a standard monorepo structure that cleanly separates the backend and frontend code.

```
signconnect/
├── .env                  # Untracked file for all secrets
├── .gitignore
├── docker-compose.yml    # Defines our PostgreSQL service
├── frontend/             # All frontend code
│   ├── index.html
│   └── script.js
├── pyproject.toml        # Poetry configuration
└── src/                  # All backend Python code
    └── signconnect/
        ├── __init__.py
        ├── main.py       # FastAPI app, endpoints, WebSocket
        ├── crud.py       # Database interaction functions
        ├── schemas.py    # Pydantic data validation models
        ├── firebase.py   # Firebase Admin initialization
        ├── llm/
        │   └── client.py # Gemini API logic
        └── db/
            ├── database.py # SQLAlchemy setup
            └── models.py   # SQLAlchemy ORM models
```

### **5. Current Status & Roadmap**

#### **What We've Completed:**

- A fully functional real-time transcription engine using Google Cloud Speech-to-Text.
    
- A secure user authentication system via Firebase.
    
- Initial integration with the Gemini API to provide generic response suggestions.
    
- A working frontend that allows users to sign up, log in, and use the core transcription service.
    
- The backend API and database models for creating personalized "Scenarios" and "Preferences."
    

#### **Where We Are Now (Our Next Step):**

We are in the process of building the frontend UI for the personalization engine. We have added the HTML for the management view and are currently debugging an error that occurs when a user tries to create a new scenario.

#### **What's Left to Do:**

1. **Fix the Current Bug:** Resolve the error preventing scenario creation.
    
2. **Complete the Personalization UI:** Fully implement the `fetchAndDisplayScenarios` function and add UI for adding questions to scenarios.
    
3. **Enhance the LLM Prompt:** Update the `llm/client.py` to use the newly fetched user preferences and vector search results to create hyper-personalized prompts for Gemini.
    
4. **Polish and Deploy:** Refine the UI, write tests, and deploy the application to the cloud.
