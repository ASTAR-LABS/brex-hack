from fastapi import APIRouter, File, UploadFile, HTTPException
from app.clients.azure_transcribe_client import AzureTranscribeClient
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize transcription client
transcribe_client = AzureTranscribeClient()


@router.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Simple endpoint to transcribe audio using gpt-4o-transcribe
    """
    try:
        # Read the audio file
        audio_data = await audio.read()
        
        # Transcribe using Azure
        result = await transcribe_client.transcribe_audio(
            audio_data,
            sample_rate=16000
        )
        
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "success": True,
            "text": result.get("text", ""),
            "is_final": True
        }
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))