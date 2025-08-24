import httpx
import os
import logging
import base64
from typing import Optional, Dict, Any
import tempfile
import wave

logger = logging.getLogger(__name__)


class AzureTranscribeClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        deployment_name: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("AZURE_TRANSCRIBE_KEY")
        self.endpoint = endpoint or os.getenv("AZURE_TRANSCRIBE_ENDPOINT")
        self.deployment_name = deployment_name or os.getenv(
            "AZURE_TRANSCRIBE_DEPLOYMENT", "gpt-4o-transcribe"
        )

        if not self.api_key or not self.endpoint:
            logger.warning(
                "Azure Transcribe credentials not configured. Transcription will not work."
            )

    async def transcribe_audio(
        self, audio_data: bytes, sample_rate: int = 16000
    ) -> Dict[str, Any]:
        """
        Transcribe audio using Azure OpenAI gpt-4o-transcribe model
        
        Args:
            audio_data: Raw PCM audio data (16-bit, mono)
            sample_rate: Sample rate of the audio (default 16000 Hz)
            
        Returns:
            Dict with transcription result
        """
        if not self.api_key or not self.endpoint:
            logger.error("Azure Transcribe credentials not configured")
            return {"text": "", "error": "Transcription service not configured"}

        try:
            # Create a temporary WAV file from the audio data
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                with wave.open(tmp_file.name, "wb") as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(audio_data)

                # Read the WAV file for sending
                with open(tmp_file.name, "rb") as f:
                    wav_data = f.read()

                # Clean up temp file
                os.unlink(tmp_file.name)

            # Prepare the API request
            url = f"{self.endpoint}/openai/deployments/{self.deployment_name}/audio/transcriptions"
            
            # Add API version if not already in URL
            if "api-version" not in url:
                url += "?api-version=2025-03-01-preview"

            headers = {
                "api-key": self.api_key,
            }

            # Prepare multipart form data
            files = {
                "file": ("audio.wav", wav_data, "audio/wav"),
            }

            data = {
                "model": "gpt-4o-transcribe",
                "response_format": "json",
                "language": "en",
            }

            # Make the API request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    files=files,
                    data=data,
                )

                if response.status_code != 200:
                    logger.error(
                        f"Azure Transcribe API error: {response.status_code} - {response.text}"
                    )
                    return {
                        "text": "",
                        "error": f"Transcription failed: {response.status_code}",
                    }

                result = response.json()
                
                # The API returns {"text": "transcribed text"}
                transcribed_text = result.get("text", "")
                
                logger.info(f"Transcribed: {transcribed_text}")
                
                return {
                    "text": transcribed_text,
                    "is_final": True,  # All transcriptions are final with this API
                }

        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return {"text": "", "error": str(e)}