from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from app.services.session_service import SessionManager
from app.services.audio_service import AudioProcessor
from app.clients.whisper_client import WhisperClient
import httpx
import os
# GitHub integration is now handled through the agent
import json
import asyncio
import logging
from datetime import datetime
import uuid


logger = logging.getLogger(__name__)


class WebSocketService:
    def __init__(self):
        from app.core.config import settings

        self.session_manager = SessionManager()
        self.whisper_client = WhisperClient(model_size=settings.whisper_model_size)
        self.agent_base_url = os.getenv("API_URL", "http://localhost:8000")

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

        # Wait for initial message with optional session_id and session_token
        session = None
        is_resumed = False
        session_token = None
        try:
            first_message = await asyncio.wait_for(websocket.receive(), timeout=5.0)
            if "text" in first_message:
                data = json.loads(first_message["text"])
                if data.get("type") == "init":
                    session_id = data.get("session_id")
                    session_token = data.get("session_token")
                    session, is_resumed = self.session_manager.create_or_resume_session(
                        websocket, session_id, metadata
                    )
                    if session_token:
                        session.metadata["session_token"] = session_token
        except asyncio.TimeoutError:
            # No init message received, create new session
            session = self.session_manager.create_session(websocket, metadata)
        except Exception as e:
            logger.warning(f"Error processing init message: {e}")
            session = self.session_manager.create_session(websocket, metadata)

        if not session:
            session = self.session_manager.create_session(websocket, metadata)

        from app.core.config import settings

        audio_processor = AudioProcessor(
            sample_rate=settings.audio_sample_rate,
            chunk_duration_ms=settings.audio_chunk_duration_ms,
            buffer_duration_ms=settings.audio_buffer_duration_ms,
            vad_aggressiveness=settings.vad_aggressiveness,
            vad_enabled=settings.vad_enabled,
        )

        await websocket.send_json(
            {
                "type": "session_started" if not is_resumed else "session_resumed",
                "session_id": session.session_id,
                "timestamp": datetime.now().isoformat(),
                "is_resumed": is_resumed,
                "transcript": session.full_transcript if is_resumed else [],
            }
        )

        try:
            while True:
                message = await websocket.receive()

                if "text" in message:
                    data = json.loads(message["text"])
                    should_stop = await self._handle_control_message(session, data)
                    if should_stop:
                        break  # Exit the loop to end the session

                elif "bytes" in message:
                    audio_chunk = message["bytes"]
                    session.audio_buffer.extend(audio_chunk)

                    audio_to_process = audio_processor.add_audio_chunk(audio_chunk)

                    if audio_to_process:
                        # Pass session-specific context and get updated context back
                        text, is_final, updated_context = (
                            await self.whisper_client.transcribe_stream(
                                audio_to_process,
                                sample_rate=16000,
                                language="en",
                                context_words=session.word_history,
                            )
                        )

                        # Update session's context with the new words
                        if is_final and updated_context:
                            session.word_history = updated_context

                        if text:
                            session.add_to_transcript(text, is_final)

                            response = {
                                "type": "transcription",
                                "text": text,
                                "is_final": is_final,
                                "session_id": session.session_id,
                                "timestamp": datetime.now().isoformat(),
                                "full_transcript": session.get_full_text(),
                            }

                            await websocket.send_json(response)

                            if is_final:
                                await websocket.send_json(
                                    {
                                        "type": "sentence_complete",
                                        "sentence": text,
                                        "total_sentences": len(session.full_transcript),
                                        "timestamp": datetime.now().isoformat(),
                                    }
                                )

                                # Extract and execute actions from the final text
                                await self._extract_and_execute_actions(
                                    text, session, websocket
                                )
                    session.update_activity()

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for session {session.session_id}")
        except Exception as e:
            logger.error(f"Error in WebSocket handler: {e}")
            # Only try to send error if websocket is still open
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": str(e),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
            except Exception as send_error:
                logger.debug(f"Could not send error message: {send_error}")
        finally:
            transcript = session.get_full_text()
            if transcript:
                logger.info(f"Session {session.session_id} transcript: {transcript}")

            # Pause session instead of removing it (will be auto-cleaned after persistence timeout)
            self.session_manager.pause_session(session.session_id)

            try:
                await websocket.close()
            except Exception as send_error:
                logger.debug(f"Could not send error message: {send_error}")

    async def _handle_control_message(self, session, data: dict):
        command = data.get("command")

        if command == "stop_recording":
            logger.info(f"Pausing session {session.session_id}")
            await session.websocket.send_json(
                {
                    "type": "session_paused",
                    "session_id": session.session_id,
                    "timestamp": datetime.now().isoformat(),
                    "final_transcript": session.get_full_text(),
                    "can_resume": True,
                    "resume_timeout_minutes": 10,
                }
            )
            return True  # Signal to pause the session

        elif command == "get_transcript":
            await session.websocket.send_json(
                {
                    "type": "transcript",
                    "full_transcript": session.full_transcript,
                    "current_buffer": session.current_buffer,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        elif command == "clear_transcript":
            session.full_transcript.clear()
            session.current_buffer = ""
            await session.websocket.send_json(
                {"type": "transcript_cleared", "timestamp": datetime.now().isoformat()}
            )

        elif command == "get_session_info":
            await session.websocket.send_json(
                {"type": "session_info", "data": session.to_dict()}
            )

        return False  # Don't stop the session for other commands

    async def _extract_and_execute_actions(
        self, text: str, session, websocket: WebSocket
    ):
        """Process text through the agent and handle tool executions"""
        try:
            # Get session token for authentication
            session_token = session.metadata.get("session_token")
            
            # Call the new agent endpoint
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.agent_base_url}/api/v1/agent/chat",
                    json={
                        "message": text,
                        "categories": ["github", "utility"],  # Enable relevant tools
                        "model": "gpt-oss-120b",
                        "session_token": session_token
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Agent API error: {response.status_code} - {response.text}")
                    await websocket.send_json({
                        "type": "action_error",
                        "message": "Failed to process your request",
                        "timestamp": datetime.now().isoformat()
                    })
                    return
                
                result = response.json()
            
            if not result.get("success"):
                logger.error(f"Agent processing failed: {result.get('error')}")
                return
            
            # Extract tools used and convert to actions format
            tools_used = result.get("tools_used", [])
            actions = []
            
            for tool_name in tools_used:
                # Convert tool usage to action format for frontend compatibility
                action_type = "github_action" if "github" in tool_name else "task"
                actions.append({
                    "type": action_type,
                    "description": f"Executed {tool_name}",
                    "confidence": 1.0
                })

            # Notify about extracted actions (for frontend compatibility)
            if actions:
                await websocket.send_json(
                    {
                        "type": "actions_extracted",
                        "actions": actions,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            
            # Send agent response as a message
            agent_response = result.get("response", "")
            if agent_response:
                await websocket.send_json(
                    {
                        "type": "agent_response",
                        "message": agent_response,
                        "tools_used": tools_used,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            
            # If GitHub tools were used, notify as action_executed for frontend
            for tool in tools_used:
                if "github" in tool.lower():
                    # Add to session's executed actions
                    action_id = str(uuid.uuid4())
                    session.add_executed_action(
                        action_id=action_id,
                        action_type="github_action",
                        description=f"Executed {tool}",
                        github_id=None  # Agent handles the actual execution
                    )
                    
                    await websocket.send_json(
                        {
                            "type": "action_executed",
                            "action": tool,
                            "result": {
                                "message": f"Successfully executed {tool}"
                            },
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

        except Exception as e:
            logger.error(f"Error extracting/executing actions: {e}")

    # GitHub action execution is now handled by the agent

    # Update actions are now handled by the agent
