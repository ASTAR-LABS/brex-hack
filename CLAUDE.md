# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
A real-time voice transcription application with:
- **Backend**: FastAPI WebSocket server with Whisper transcription (Python)
- **Frontend**: Next.js React app with live audio visualization

## Common Development Commands

### Backend (Python/FastAPI)
```bash
# Setup virtual environment
python3.13 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run server
python backend/run.py
# or
uvicorn app.main:app --reload
```

### Frontend (Next.js/React)
```bash
# Install dependencies
cd frontend && npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run linting
npm run lint
```

## Architecture

### Backend Structure
- **app/api/v1/**: WebSocket and REST endpoints (routes only)
- **app/clients/**: External service integrations (Whisper, Azure OpenAI)
- **app/services/**: Business logic (audio processing, VAD, session management, WebSocket handling)
- **app/core/**: Configuration and settings
- **app/main.py**: FastAPI application entry point

Key endpoints:
- WebSocket: `ws://localhost:8000/api/v1/ws/audio`
- Health: `GET /health`
- Sessions: `GET /api/v1/sessions`

### Frontend Structure
- **app/**: Next.js app router pages and layouts
- **app/page.tsx**: Main voice recording interface with waveform visualization
- Uses Tailwind CSS for styling
- TypeScript for type safety

## WebSocket Protocol
The application uses WebSocket for real-time audio streaming:

**Client → Server**: Binary PCM audio (16kHz, 16-bit) or JSON commands
**Server → Client**: JSON transcription results with session info

## Environment Configuration
Backend requires `.env` file with Azure OpenAI credentials:
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_VERSION`
- `AZURE_OPENAI_DEPLOYMENT_NAME`

## Key Technologies
- **Backend**: FastAPI, uvicorn, pywhispercpp, webrtcvad, OpenAI SDK
- **Frontend**: Next.js 15.5, React 19.1, Tailwind CSS, TypeScript
- **Audio**: Voice Activity Detection (VAD), 16kHz PCM audio processing