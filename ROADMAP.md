
---

## Project Recap: SignConnect

### **1. The Vision & Core Mission**

- **Project Name:** SignConnect
    
- **Mission:** To build an assistive Progressive Web App (PWA) that empowers deaf and non-verbal individuals by providing real-time, AI-powered communication support.
    
- **Core Loop:** The application listens to spoken language, transcribes it to text, and suggests relevant, personalized responses for the user.
    
- **End Goal:** A high-impact portfolio project demonstrating a wide range of modern software engineering skills, with the potential to become a real-world SaaS business.
    

### **2. Development Environment & Tools**

- **Backend Framework:** **Python** with **FastAPI** for creating a high-performance, asynchronous API.
    
- **Frontend Language:** **JavaScript**, along with HTML and CSS. The UI is currently built with vanilla JS, with the possibility of adopting a framework like React later.
    
- **Database:** **PostgreSQL** running in a **Docker** container. We are using the `ankane/pgvector` image to enable vector search capabilities.
    
- **Dependency Management:** **Poetry** for managing all Python packages and project dependencies in a `pyproject.toml` file.

### **3. Workflow & Methods**

- **Version Control:** We are using **Git** and pushing our code to a remote repository on **GitHub**.
    
- **Authentication:** We have pivoted to a professional, third-party authentication service, **Firebase Authentication**, to securely manage all user sign-up, login, and identity verification. We are using Firebase ID tokens (JWTs) to secure our backend.
    
- **API Testing:** We are using **Postman** to manually test our API endpoints as we build them, ensuring they work correctly before integrating them with the frontend.
    
- **Database Migrations:** For our current development phase, we are handling database schema changes by manually resetting the Docker volume. As the project matures, we would implement a formal migration tool like **Alembic**.


### **4. Current Status & Roadmap**

## What We've Completed (The Foundation)

We have successfully built a robust foundation. We have:

- **A Scalable Backend Architecture:** Built with Python and FastAPI, using a professional src layout and Poetry for dependency management.
    
- **A Dockerized Database:** A PostgreSQL database running in Docker, ready to store application data.
    
- **Real-Time Transcription Engine:** A secure WebSocket that captures microphone audio from the frontend and uses the Google Cloud Speech-to-Text API to produce a live, "real-time typing" transcript.
    
- **Secure User Management:** A complete pivot to a professional, third-party authentication system (Firebase Authentication) to securely manage user sign-up and login, protecting our application with verified identity tokens.
    
- **Initial AI Suggestions:** A successful integration with the Gemini API to take a final transcript and generate relevant response suggestions.
    
- **A Functional Frontend:** An interactive web interface that successfully ties all these backend services together, displaying the live transcript and clickable suggestion buttons.

- **Implemented Contextual Understanding via Vector Search:** Integrated a vector database extension (pgvector) to store user-defined questions. When a new transcript comes in, we convert it to a vector embedding and perform a semantic search to find the most similar question the user has already prepared.

- **Enhance the AI Prompt:** Upgraded our call to the Gemini API. Instead of just sending the transcript, we send a rich prompt containing the transcript + user preferences + the results of the vector search. This allows Gemini to provide hyper-relevant, personalized suggestions.

- **Robust Testing Suite:** Unit and integration tests for solid test coverage.
    

#### **5. Where We Are Now (Our Next Step):**

**User Free Response:** If none of the responses suggested by the LLM are suitable answers to the question being asked, the user has a space to fill in a response with their keyboard. This becomes a new question:answer and saved to the database.

#### **6. What's Left to Do:**

- LLM suggestions for possible questions user may encounter for upcoming scenario. User is presented with possible questions and those they choose to answer are saved as question:answer pairs in that respective scenario. 
- Design Transcript flow for conversation: when a new conversation kicks of, the history should be saved as the conversation continues to allow context into what has been said.
- Post Conversation: Users should be able to take a previous/completed conversation, and turn that into question:response pairs to save to their profile. User context should grow and recommendations improve the more the service is used.
- Refine the UI/UX to be clean, intuitive, and accessible.
- Integrate payment processor for membership service.
- Write comprehensive documentation (README, API docs).
- Implement improved logging
- Containerize the FastAPI application using Docker.
- Write Kubernetes deployment manifests (`Deployment`, `Service`, `Ingress`) to deploy containers to existing Oracle Cloud cluster.
- Set up a CI/CD pipeline using GitHub Actions to automate testing and deployment to ArgoCD.

**Polish, Deploy, Iterate (continuous loop):** Refine the UI, write tests, refactor code, and deploy the application to the cloud.
