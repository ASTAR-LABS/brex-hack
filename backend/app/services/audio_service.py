import numpy as np
from typing import Optional, Tuple, List
import struct
import logging
from collections import deque
import webrtcvad

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_duration_ms: int = 30,
        buffer_duration_ms: int = 500,
        vad_aggressiveness: int = 2,
        vad_enabled: bool = False
    ):
        self.sample_rate = sample_rate
        self.chunk_duration_ms = chunk_duration_ms
        self.buffer_duration_ms = buffer_duration_ms
        
        self.chunk_size = int(sample_rate * chunk_duration_ms / 1000) * 2
        self.buffer_size = int(sample_rate * buffer_duration_ms / 1000) * 2
        
        self.audio_buffer = bytearray()
        self.processing_buffer = deque(maxlen=int(buffer_duration_ms / chunk_duration_ms))
        
        self.vad_enabled = vad_enabled
        
        if self.vad_enabled:
            try:
                self.vad = webrtcvad.Vad(vad_aggressiveness)
            except:
                logger.warning("WebRTC VAD not available, continuing without VAD")
                self.vad = None
                self.vad_enabled = False
        else:
            self.vad = None
            logger.info("VAD disabled by configuration")
        
        self.speech_frames = 0
        self.silence_frames = 0
        self.is_speech_active = False
        self.speech_threshold = 0.3  # Lowered from 0.5 to detect softer speech
        self.silence_threshold = 0.9
        
    def add_audio_chunk(self, audio_data: bytes) -> Optional[bytes]:
        self.audio_buffer.extend(audio_data)
        
        if len(self.audio_buffer) >= self.buffer_size:
            audio_to_process = bytes(self.audio_buffer[:self.buffer_size])
            self.audio_buffer = self.audio_buffer[self.buffer_size:]
            
            if self.vad_enabled and self.vad:
                if self._detect_speech(audio_to_process):
                    return audio_to_process
                elif self.is_speech_active:
                    return audio_to_process
            else:
                return audio_to_process
        
        return None
    
    def _detect_speech(self, audio_data: bytes) -> bool:
        if not self.vad or not self.vad_enabled:
            return True
        
        frames = self._chunk_audio(audio_data, self.chunk_duration_ms)
        speech_count = 0
        
        for frame in frames:
            if len(frame) == self.chunk_size:
                try:
                    is_speech = self.vad.is_speech(frame, self.sample_rate)
                    if is_speech:
                        speech_count += 1
                except:
                    return True
        
        speech_ratio = speech_count / len(frames) if frames else 0
        
        if speech_ratio > self.speech_threshold:
            self.speech_frames += 1
            self.silence_frames = 0
            if self.speech_frames >= 2:  # Faster speech detection
                self.is_speech_active = True
        else:
            self.silence_frames += 1
            self.speech_frames = 0
            if self.silence_frames >= 30:  # Much more conservative - ~900ms of silence
                self.is_speech_active = False
        
        return self.is_speech_active
    
    def _chunk_audio(self, audio_data: bytes, chunk_duration_ms: int) -> List[bytes]:
        chunk_size = int(self.sample_rate * chunk_duration_ms / 1000) * 2
        chunks = []
        
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            if len(chunk) == chunk_size:
                chunks.append(chunk)
        
        return chunks
    
    def bytes_to_float32(self, audio_bytes: bytes) -> np.ndarray:
        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
        audio_float32 = audio_int16.astype(np.float32) / 32768.0
        return audio_float32
    
    def float32_to_bytes(self, audio_float32: np.ndarray) -> bytes:
        audio_int16 = (audio_float32 * 32768).astype(np.int16)
        return audio_int16.tobytes()
    
    def resample_if_needed(self, audio_data: bytes, input_sample_rate: int) -> bytes:
        if input_sample_rate == self.sample_rate:
            return audio_data
        
        import scipy.signal as signal
        
        audio_float = self.bytes_to_float32(audio_data)
        
        num_samples = len(audio_float)
        duration = num_samples / input_sample_rate
        new_num_samples = int(duration * self.sample_rate)
        
        resampled = signal.resample(audio_float, new_num_samples)
        
        return self.float32_to_bytes(resampled)
    
    def get_buffer_duration_seconds(self) -> float:
        return len(self.audio_buffer) / (self.sample_rate * 2)
    
    def clear_buffer(self):
        self.audio_buffer.clear()
        self.processing_buffer.clear()
        self.speech_frames = 0
        self.silence_frames = 0
        self.is_speech_active = False
    
    def is_buffer_ready(self) -> bool:
        return len(self.audio_buffer) >= self.buffer_size