# Multi-Agent AI Tutoring System

A multi-agent AI tutoring system based on Google's Agent Development Kit (ADK) principles and A2A (Agent-to-Agent) communication protocol. The system features a delegating Tutor Agent, specialized Math and Physics sub-agents, tool integration, and Gemini API integration.

## Project Overview

This system demonstrates the power of agent delegation and tool utilization in delivering focused, accurate academic support across different disciplines. The core architecture follows the agent delegation pattern, where a central "Tutor Agent" receives user queries and intelligently routes them to specialized "Sub-Agents" capable of handling specific domains (Math, Physics).

## Key Features

- **Tutor Agent**: Analyzes user queries and delegates to specialized sub-agents
- **Math Agent**: Handles mathematical queries with calculator tool integration
- **Physics Agent**: Handles physics-related queries with lookup tool for constants/formulas
- **Tool Integration**: Calculator and Lookup tools implemented using ADK's BaseTool framework
- **Gemini API Integration**: All agent responses generated using the Google Gemini API
- **Web Interface**: Simple UI for submitting queries and receiving responses

## Technology Stack

- **Backend**: Python, FastAPI, ADK
- **Frontend**: Next.js, React, TypeScript, Tailwind CSS
- **Database**: MongoDB with Beanie ODM
- **Deployment**: Vercel (planned)

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Google Gemini API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/SarthakB11/multi-agent-tutoring-bot.git
cd multi-agent-tutoring-bot
```

2. Install backend dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env file with your Gemini API key, MongoDB connection string, and other configuration
```

4. Run the backend server:
```bash
uvicorn src.api.main:app --reload
```

5. Install and run the frontend (React or Next.js):

   For the original React frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

   For the Next.js frontend:
   ```bash
   cd frontend-next
   npm install
   npm run dev
   ```

   Alternatively, use the run script to start both backend and frontend:
   ```bash
   ./run.sh
   ```

## Project Structure

```
multi-agent-tutoring-bot/
├── src/
│   ├── agents/            # Agent implementations
│   ├── tools/             # Tool implementations
│   ├── api/               # API endpoints
│   ├── utils/             # Utility functions (including MongoDB)
│   ├── config/            # Configuration
│   ├── models/            # Data models
│   └── tests/             # Tests
├── frontend/              # Original React frontend
├── frontend-next/        # Migrated Next.js frontend
├── requirements.txt       # Python dependencies
├── run.sh                # Run script for local development
├── MIGRATION.md          # Migration documentation
└── README.md             # Project documentation
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
