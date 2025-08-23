from pywhispercpp.model import Model
import asyncio
from typing import Tuple, Optional, List
from collections import deque
import tempfile
import wave
import os
import logging

logger = logging.getLogger(__name__)

class WhisperClient:
    def __init__(self, model_size: str = "base", n_threads: int = 6):
        self.model = Model(model_size, n_threads=n_threads)
        self.previous_text = ""
        self.overlap_duration = 0.5
        self.context_buffer = deque(maxlen=5)  # Efficient O(1) operations with automatic size limit
    
    async def transcribe(self, audio_path: str, language: str = "en") -> str:
        segments = await asyncio.to_thread(
            self.model.transcribe, 
            audio_path,
            language=language,
            print_realtime=False
        )
        text = " ".join([segment.text for segment in segments])
        return text
    
    async def transcribe_stream(
        self, 
        audio_data: bytes, 
        sample_rate: int = 16000,
        language: str = "en",
        return_timestamps: bool = False
    ) -> Tuple[str, bool]:
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                with wave.open(tmp_file.name, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(audio_data)
                
                # Use context from previous segments for better accuracy
                # Convert last 3 items from deque to list for joining
                initial_prompt = " ".join(list(self.context_buffer)[-3:]) if self.context_buffer else ""
                
                segments = await asyncio.to_thread(
                    self.model.transcribe,
                    tmp_file.name,
                    language=language,
                    print_realtime=False,
                    single_segment=True,  # Useful for streaming
                    initial_prompt=initial_prompt  # Provide context
                )
                
                os.unlink(tmp_file.name)
                
                if not segments:
                    return "", False
                
                full_text = " ".join([segment.text.strip() for segment in segments])
                
                is_final = self._is_sentence_complete(full_text)
                
                if is_final and full_text != self.previous_text:
                    self.previous_text = full_text
                    # Add to context buffer (deque automatically maintains size limit)
                    self.context_buffer.append(full_text)
                    return full_text, True
                else:
                    return full_text, False
                    
        except Exception as e:
            logger.error(f"Error in stream transcription: {e}")
            return "", False
    
    def _is_sentence_complete(self, text: str) -> bool:
        if not text:
            return False
        
        text = text.strip()
        
        sentence_endings = ['.', '!', '?', '。', '！', '？']
        
        if any(text.endswith(ending) for ending in sentence_endings):
            return True
        
        pause_indicators = [',', ';', ':', '、', '；', '：']
        words = text.split()
        if len(words) > 10 and any(char in text for char in pause_indicators):
            return True
        
        if len(words) > 15:
            return True
        
        return False