from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from app.services.session_service import SessionManager
from app.services.audio_service import AudioProcessor
from app.clients.whisper_client import WhisperClient
from app.services.action_extraction_service import ActionExtractionService
from app.integrations.github_integration import GitHubIntegration
from app.core.database import get_db, IntegrationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
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
        self.action_service = ActionExtractionService()
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
                        print(session.word_history)
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
                                await websocket.send_json({
                                    "type": "sentence_complete",
                                    "sentence": text,
                                    "total_sentences": len(session.full_transcript),
                                    "timestamp": datetime.now().isoformat()
                                })
                                
                                # Extract and execute actions from the final text
                                await self._extract_and_execute_actions(text, session, websocket)
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
            await session.websocket.send_json({
                "type": "session_info",
                "data": session.to_dict()
            })
        
        return False  # Don't stop the session for other commands
    
    async def _extract_and_execute_actions(self, text: str, session, websocket: WebSocket):
        """Extract actions from text and execute high-confidence GitHub actions"""
        try:
            # Extract actions from the text
            result = await self.action_service.extract_actions(text)
            
            if "error" in result:
                logger.error(f"Action extraction error: {result['error']}")
                return
            
            actions = result.get("actions", [])
            
            # Notify about extracted actions
            if actions:
                await websocket.send_json({
                    "type": "actions_extracted",
                    "actions": actions,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Execute high-confidence GitHub actions
            for action in actions:
                if action["type"] == "github_action" and action["confidence"] > 0.8:
                    await self._execute_github_action(action, session, websocket)
                    
        except Exception as e:
            logger.error(f"Error extracting/executing actions: {e}")
    
    async def _execute_github_action(self, action: dict, session, websocket: WebSocket):
        """Execute a GitHub action using stored credentials"""
        try:
            session_token = session.metadata.get("session_token")
            
            if not session_token:
                await websocket.send_json({
                    "type": "action_error",
                    "message": "No GitHub credentials configured. Please connect GitHub in settings.",
                    "timestamp": datetime.now().isoformat()
                })
                return
            
            # Get credentials from database
            from app.core.database import async_session_factory
            async with async_session_factory() as db:
                result = await db.execute(
                    select(IntegrationCredentials).where(
                        IntegrationCredentials.session_token == session_token
                    )
                )
                creds = result.scalar_one_or_none()
                
                if not creds or not creds.github_token:
                    await websocket.send_json({
                        "type": "action_error",
                        "message": "GitHub credentials not found. Please reconnect GitHub.",
                        "timestamp": datetime.now().isoformat()
                    })
                    return
                
                # Initialize GitHub integration
                github = GitHubIntegration(
                    token=creds.github_token,
                    owner=creds.github_owner,
                    repo=creds.github_repo
                )
                
                # Parse the action description to determine what to do
                description = action["description"].lower()
                
                if "issue" in description:
                    # Extract title from description
                    title = action["description"]
                    if "create" in description:
                        title = title.replace("create", "").replace("issue", "").strip()
                        title = title.replace("a ", "").replace("an ", "").strip()
                        title = title.replace("about", "-").replace("for", "-").strip()
                        title = title.strip("- ").capitalize()
                    
                    if not title:
                        title = "New Issue"
                    
                    # Create the issue
                    result = await github.create_issue(
                        title=title,
                        body=f"Created via voice command: {action['description']}\n\n---\n*Generated by Ultrathink*"
                    )
                    
                    if "error" not in result:
                        await websocket.send_json({
                            "type": "action_executed",
                            "action": "github_issue_created",
                            "result": {
                                "issue_number": result.get("number"),
                                "issue_url": result.get("html_url"),
                                "title": result.get("title")
                            },
                            "timestamp": datetime.now().isoformat()
                        })
                        logger.info(f"Created GitHub issue #{result.get('number')}: {result.get('title')}")
                    else:
                        await websocket.send_json({
                            "type": "action_error",
                            "message": f"Failed to create issue: {result['error']}",
                            "timestamp": datetime.now().isoformat()
                        })
                
                elif "pr" in description or "pull request" in description:
                    # Handle PR comments
                    pr_number = 1  # Default PR number, could extract from description
                    
                    result = await github.create_pr_comment(
                        pr_number=pr_number,
                        body=action["description"]
                    )
                    
                    if "error" not in result:
                        await websocket.send_json({
                            "type": "action_executed",
                            "action": "github_pr_comment_created",
                            "result": {
                                "pr_number": pr_number,
                                "comment_url": result.get("html_url")
                            },
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        await websocket.send_json({
                            "type": "action_error",
                            "message": f"Failed to create PR comment: {result['error']}",
                            "timestamp": datetime.now().isoformat()
                        })
                
        except Exception as e:
            logger.error(f"Error executing GitHub action: {e}")
            await websocket.send_json({
                "type": "action_error",
                "message": f"Failed to execute action: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
