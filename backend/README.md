# Agent Jam Voice Assistant Backend

Real-time audio transcription service using FastAPI, WebSockets, and Whisper.

## Architecture

```
backend/
├── app/
│   ├── api/                    # API endpoints (routes only)
│   │   └── v1/
│   │       ├── endpoints/      # WebSocket and REST endpoints
│   │       └── router.py       # Main API router
│   │
│   ├── clients/                # External service integrations
│   │   ├── whisper_client.py   # Whisper transcription client
│   │   └── azure_openai_client.py  # Azure OpenAI client
│   │
│   ├── core/                   # Core functionality
│   │   └── config.py          # Application settings
│   │
│   ├── services/               # Business logic
│   │   ├── audio_service.py   # Audio processing with VAD
│   │   ├── session_service.py # Session management
│   │   └── websocket_service.py # WebSocket handler logic
│   │
│   └── main.py                # FastAPI application
│
├── static/                     # Static files
│   └── test_websocket.html   # WebSocket test client
│
├── .env.example               # Environment variables template
├── requirements.txt           # Python dependencies
└── run.py                     # Application runner

```

## Setup

1. **Create virtual environment:**
```bash
python3.13 -m venv venv
source venv/bin/activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your Azure OpenAI credentials
```

4. **Run the server:**
```bash
python run.py
# or
uvicorn app.main:app --reload
```

## API Endpoints

- **WebSocket:** `ws://localhost:8000/api/v1/ws/audio`
- **Health Check:** `GET /health`
- **Active Sessions:** `GET /api/v1/sessions`

## WebSocket Protocol

### Client → Server
- **Audio Data:** Binary PCM audio (16kHz, 16-bit)
- **Control Commands:** JSON messages
  ```json
  {
    "command": "get_transcript" | "clear_transcript" | "get_session_info"
  }
  ```

### Server → Client
- **Transcription Results:**
  ```json
  {
    "type": "transcription",
    "text": "transcribed text",
    "is_final": true/false,
    "session_id": "uuid",
    "timestamp": "iso-datetime",
    "full_transcript": "complete session text"
  }
  ```

## Testing

Open `static/test_websocket.html` in a browser to test real-time transcription.

## Features

- Real-time audio streaming over WebSocket
- Voice Activity Detection (VAD) for optimized processing
- Session management with automatic cleanup
- Sentence boundary detection
- Full transcript buffering per session
- Clean architecture with separated concerns