from fastapi import WebSocket, WebSocketDisconnect
from app.services.session_service import SessionManager
from app.services.audio_service import AudioProcessor
from app.clients.whisper_client import WhisperClient
import json
import asyncio
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class WebSocketService:
    def __init__(self):
        self.session_manager = SessionManager()
        self.whisper_client = WhisperClient()
        
    async def start(self):
        await self.session_manager.start()
    
    async def stop(self):
        await self.session_manager.stop()
    
    async def handle_audio_connection(self, websocket: WebSocket):
        await websocket.accept()
        
        metadata = {
            "user_agent": websocket.headers.get("user-agent", ""),
            "origin": websocket.headers.get("origin", ""),
        }
        
        session = self.session_manager.create_session(websocket, metadata)
        audio_processor = AudioProcessor()
        
        await websocket.send_json({
            "type": "session_started",
            "session_id": session.session_id,
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            while True:
                message = await websocket.receive()
                
                if "text" in message:
                    data = json.loads(message["text"])
                    await self._handle_control_message(session, data)
                    
                elif "bytes" in message:
                    audio_chunk = message["bytes"]
                    session.audio_buffer.extend(audio_chunk)
                    
                    audio_to_process = audio_processor.add_audio_chunk(audio_chunk)
                    
                    if audio_to_process:
                        text, is_final = await self.whisper_client.transcribe_stream(
                            audio_to_process,
                            sample_rate=16000,
                            language="en"
                        )
                        
                        if text:
                            session.add_to_transcript(text, is_final)
                            
                            response = {
                                "type": "transcription",
                                "text": text,
                                "is_final": is_final,
                                "session_id": session.session_id,
                                "timestamp": datetime.now().isoformat(),
                                "full_transcript": session.get_full_text()
                            }
                            
                            await websocket.send_json(response)
                            
                            if is_final:
                                await websocket.send_json({
                                    "type": "sentence_complete",
                                    "sentence": text,
                                    "total_sentences": len(session.full_transcript),
                                    "timestamp": datetime.now().isoformat()
                                })
                    
                    session.update_activity()
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for session {session.session_id}")
        except Exception as e:
            logger.error(f"Error in WebSocket handler: {e}")
            # Only try to send error if websocket is still open
            try:
                if websocket.client_state.value == 1:  # WebSocketState.CONNECTED
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
            except:
                pass
        finally:
            transcript = session.get_full_text()
            if transcript:
                logger.info(f"Session {session.session_id} transcript: {transcript}")
            
            self.session_manager.remove_session(session.session_id)
            
            try:
                await websocket.close()
            except:
                pass
    
    async def _handle_control_message(self, session, data: dict):
        command = data.get("command")
        
        if command == "get_transcript":
            await session.websocket.send_json({
                "type": "transcript",
                "full_transcript": session.full_transcript,
                "current_buffer": session.current_buffer,
                "timestamp": datetime.now().isoformat()
            })
        
        elif command == "clear_transcript":
            session.full_transcript.clear()
            session.current_buffer = ""
            await session.websocket.send_json({
                "type": "transcript_cleared",
                "timestamp": datetime.now().isoformat()
            })
        
        elif command == "get_session_info":
            await session.websocket.send_json({
                "type": "session_info",
                "data": session.to_dict()
            })