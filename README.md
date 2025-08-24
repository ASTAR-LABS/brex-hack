# Commute Commander 🎙️

> Transform your commute into productive development time with voice-powered coding assistance

## Overview

We've all been there - stuck in traffic or on public transit during our daily commute, wishing we could be productive but limited by clunky voice assistants that barely understand context or can't access our development tools. Siri might set a timer, but can it review your pull requests or create GitHub issues? Not a chance.

We built a powerful voice-first productivity system that actually understands developers. Using local Whisper transcription for privacy and speed, combined with GPT-4 for intelligent task execution, we've created a hands-free way to stay productive anywhere.

## ✨ Features

- **Lightning-fast local transcription** using Whisper-cpp for low-latency voice recognition
- **Intelligent command understanding** via GPT-4 that grasps context and developer intent  
- **MCP (Model Context Protocol) integration** - connect any tool you already use
- **Real-time execution** - create GitHub issues, review PRs, manage tasks - all with your voice

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Node.js 18+
- Azure OpenAI API credentials

### Backend Setup

```bash
# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp .env.example .env
# Add your Azure OpenAI credentials to .env

# Run the server
python backend/run.py
```

### Frontend Setup

```bash
# Install dependencies
cd frontend
npm install

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and start talking!

## 🏗️ Architecture

### Backend (FastAPI + Python)
- WebSocket server for real-time audio streaming
- Local Whisper transcription via pywhispercpp
- Voice Activity Detection (VAD) for smart audio chunking
- Azure OpenAI integration for intelligent command processing
- MCP support for tool integrations

### Frontend (Next.js + React)
- Real-time audio capture and visualization
- Live transcription display
- Action execution feedback
- Minimal, distraction-free interface

## 🎯 Use Cases

- **Code Review on the Go**: "Show me the latest pull requests and summarize the changes"
- **Issue Management**: "Create a bug issue for the login page crash"
- **Task Planning**: "Add a TODO to refactor the authentication service"
- **Documentation**: "Update the README with the new API endpoints"
- **Team Communication**: "Send a message to the team about the deployment status"

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=your-endpoint
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment
```

### MCP Tools

Configure your MCP tools in `backend/app/core/config.py` to enable additional integrations.

## 🛠️ Tech Stack

- **Transcription**: Whisper-cpp (local, fast, accurate)
- **AI**: Azure OpenAI GPT-4
- **Backend**: FastAPI, WebSockets, Python
- **Frontend**: Next.js, React, TypeScript
- **Audio**: WebRTC VAD, 16kHz PCM processing
- **Integrations**: MCP (Model Context Protocol)

## 📁 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/          # WebSocket and REST endpoints
│   │   ├── clients/      # External service integrations
│   │   ├── services/     # Business logic
│   │   └── core/         # Configuration
│   └── requirements.txt
├── frontend/
│   ├── app/              # Next.js app router
│   ├── components/       # React components
│   └── package.json
└── README.md
```

## 🤝 Contributing

We welcome contributions! Whether it's adding new MCP tools, improving transcription accuracy, or enhancing the UI - every bit helps.

## 📜 License

MIT

---

**Built for developers, by developers who hate wasting their commute.**