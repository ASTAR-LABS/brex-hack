from pywhispercpp.model import Model
import asyncio
from typing import Tuple, Optional, List
import tempfile
import wave
import os
import logging

logger = logging.getLogger(__name__)

class WhisperClient:
    def __init__(self, model_size: str = "base", n_threads: int = 6):
        self.model = Model(model_size, n_threads=n_threads)
        # Removed instance-level state to make WhisperClient stateless and thread-safe
    
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
        context_words: Optional[List[str]] = None,
        return_timestamps: bool = False
    ) -> Tuple[str, bool, List[str]]:
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                with wave.open(tmp_file.name, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(audio_data)
                
                # Use provided context words (last 100 words max to stay under 224 token limit)
                # Initialize context if not provided
                if context_words is None:
                    context_words = []
                
                # Take last 100 words to ensure we stay under 224 token limit
                context_words = context_words[-100:] if len(context_words) > 100 else context_words
                initial_prompt = " ".join(context_words) if context_words else ""
                
                segments = await asyncio.to_thread(
                    self.model.transcribe,
                    tmp_file.name,
                    language=language,
                    print_realtime=False,
                    single_segment=True,  # Useful for streaming
                    initial_prompt=initial_prompt,  # Provide context
                    # Optimal parameters for whisper.cpp
                    beam_size=2,  # Optimal for whisper.cpp (not 5)
                    temperature=0.0,  # Deterministic output
                    no_speech_threshold=0.6,  # Filter silence
                    compression_ratio_threshold=2.4,  # Reject gibberish
                    suppress_blank=True,  # Suppress blank outputs
                    suppress_non_speech_tokens=True  # Remove [MUSIC] etc
                )
                
                os.unlink(tmp_file.name)
                
                if not segments:
                    return "", False, context_words
                
                # Quality filtering
                for segment in segments:
                    # Check if transcription quality metrics are available
                    if hasattr(segment, 'no_speech_prob') and segment.no_speech_prob > 0.6:
                        logger.debug("High no_speech probability, skipping")
                        return "", False, context_words
                    
                    # Log compression ratio for debugging
                    if hasattr(segment, 'compression_ratio'):
                        logger.debug(f"Compression ratio: {segment.compression_ratio}")
                        if segment.compression_ratio > 2.4:
                            logger.warning("Likely gibberish (high compression ratio), rejecting")
                            return "", False, context_words
                
                full_text = " ".join([segment.text.strip() for segment in segments])
                
                is_final = self._is_sentence_complete(full_text)
                
                # Update context with new words if we have final text
                updated_context = list(context_words)  # Create a copy
                if is_final and full_text.strip():
                    new_words = full_text.split()
                    updated_context.extend(new_words)
                    # Keep only last 100 words
                    updated_context = updated_context[-100:]
                
                return full_text, is_final, updated_context
                    
        except Exception as e:
            logger.error(f"Error in stream transcription: {e}")
            return "", False, context_words if context_words else []
    
    def _is_sentence_complete(self, text: str) -> bool:
        if not text:
            return False
        
        text = text.strip()
        
        # Don't mark very short text as complete
        if len(text) < 20:  # Characters, not words
            return False
        
        # Trust Whisper's punctuation for sentence endings
        sentence_endings = ['.', '!', '?', '。', '！', '？']
        if any(text.endswith(ending) for ending in sentence_endings):
            return True
        
        # Only force completion for very long text without punctuation
        words = text.split()
        if len(words) > 25:  # Much higher threshold
            return True
        
        return False