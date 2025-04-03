# SignConnect

<div align="center">
  <img src="https://via.placeholder.com/150" alt="SignConnect Logo" width="150"/>
  <h3>Breaking communication barriers for the deaf community</h3>
</div>

## 📝 Project Overview

SignConnect is an assistive technology web application designed to help deaf and hard-of-hearing individuals navigate everyday conversations with ease. Using speech-to-text technology and AI-powered response suggestions, SignConnect creates a seamless bridge between spoken language and text-based communication.

### 🎯 The Problem

For deaf and hard-of-hearing individuals, spontaneous conversations can be challenging, especially in environments where:
- Communication partners don't know sign language
- Note-passing is impractical or too slow
- Professional interpreters aren't available

### 💡 Our Solution

SignConnect transforms spoken language into text in real-time and provides intelligent, contextual response suggestions based on the user's preferences and conversation history.

## ✨ Key Features

- **Real-time Speech-to-Text**: Instantly convert spoken words into readable text
- **Context-Aware Response Suggestions**: Get personalized response options based on the conversation context
- **Scenario-Based Support**: Pre-configure responses for common situations like restaurants, medical appointments, or workplace meetings
- **User Preferences**: Store favorites, commonly used phrases, and personal details for quick access
- **Offline Capabilities**: Continue using core features even without internet connectivity
- **Vector-Based Semantic Matching**: Understand the meaning behind questions for more accurate response suggestions

## 🛠️ Technology Stack

- **Frontend**: React.js (Progressive Web App)
- **Backend**: Node.js with Express
- **Database**: PostgreSQL with pgvector extension for semantic search
- **Speech Processing**: Web Speech API / OpenAI Whisper API
- **Vector Embeddings**: OpenAI Embeddings API
- **Deployment**: AWS/GCP/Azure (TBD)

## 🚀 Development Roadmap

SignConnect is being developed in phases:

- **Phase 1**: Foundation & Basic Functionality
- **Phase 2**: Intelligence & Personalization
- **Phase 3**: Advanced Features & Polish
- **Phase 4**: Portfolio Enhancement

*For detailed milestone information, see [ROADMAP.md](./ROADMAP.md)*

## 🧩 System Architecture

SignConnect follows a modern, scalable architecture:

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│                 │     │                  │     │                 │
│  React Frontend │◄────┤  Express Backend │◄────┤  PostgreSQL DB  │
│    (PWA)        │     │                  │     │  with pgvector  │
│                 │     │                  │     │                 │
└────────┬────────┘     └────────┬─────────┘     └─────────────────┘
         │                       │
         │                       │
┌────────▼────────┐     ┌────────▼─────────┐
│                 │     │                  │
│  Speech-to-Text │     │  Vector Search   │
│    Service      │     │    Service       │
│                 │     │                  │
└─────────────────┘     └──────────────────┘
```

## 🔍 Getting Started

### Prerequisites
- Node.js (v16+)
- npm or yarn
- PostgreSQL (v13+)

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/HowDiggy/SignConnect.git
   cd SignConnect
   ```

2. Install dependencies
   ```bash
   # Install frontend dependencies
   cd frontend
   npm install
   
   # Install backend dependencies
   cd ../backend
   npm install
   ```

3. Set up environment variables
   ```bash
   # Create .env files in both frontend and backend directories
   # See .env.example for required variables
   ```

4. Set up the database
   ```bash
   # Run PostgreSQL setup scripts
   npm run db:setup
   ```

5. Start the development servers
   ```bash
   # In the backend directory
   npm run dev
   
   # In the frontend directory (in a separate terminal)
   npm start
   ```

## 📊 Project Status

SignConnect is currently in early development. This project is being built as a portfolio piece to demonstrate full-stack development skills.

## 🧪 Testing

```bash
# Run backend tests
cd backend
npm test

# Run frontend tests
cd frontend
npm test
```

## 🤝 Contributing

This project is currently a personal portfolio project and not open for contributions.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Paulo Jauregui** - [GitHub Profile](https://github.com/HowDiggy)

---

<div align="center">
  <i>SignConnect: Bringing the conversation to everyone.</i>
</div>
