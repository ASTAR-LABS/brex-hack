'use client';

import { useState, useRef, useCallback } from 'react';

export function useSimpleRecording() {
  const [isRecording, setIsRecording] = useState(false);
  const [transcriptions, setTranscriptions] = useState<string[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  
  const audioContextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioBufferRef = useRef<Float32Array[]>([]);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  // Convert Float32Array to WAV
  const convertToWav = (audioData: Float32Array[], sampleRate: number): Blob => {
    // Concatenate all audio chunks
    const totalLength = audioData.reduce((acc, chunk) => acc + chunk.length, 0);
    const fullAudio = new Float32Array(totalLength);
    let offset = 0;
    for (const chunk of audioData) {
      fullAudio.set(chunk, offset);
      offset += chunk.length;
    }
    
    // Convert to 16-bit PCM
    const pcmData = new Int16Array(fullAudio.length);
    for (let i = 0; i < fullAudio.length; i++) {
      pcmData[i] = Math.max(-32768, Math.min(32767, fullAudio[i] * 32768));
    }
    
    // Create WAV header
    const wavBuffer = new ArrayBuffer(44 + pcmData.length * 2);
    const view = new DataView(wavBuffer);
    
    // Helper to write string
    const writeString = (offset: number, string: string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };
    
    // WAV header
    writeString(0, 'RIFF');
    view.setUint32(4, 36 + pcmData.length * 2, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(36, 'data');
    view.setUint32(40, pcmData.length * 2, true);
    
    // Write PCM data
    const dataView = new Int16Array(wavBuffer, 44);
    dataView.set(pcmData);
    
    return new Blob([wavBuffer], { type: 'audio/wav' });
  };
  
  // Send audio to backend for transcription
  const sendAudioForTranscription = useCallback(async () => {
    if (audioBufferRef.current.length === 0) return;
    
    setIsProcessing(true);
    
    try {
      const sampleRate = audioContextRef.current?.sampleRate || 16000;
      const wavBlob = convertToWav(audioBufferRef.current, sampleRate);
      
      // Clear buffer
      audioBufferRef.current = [];
      
      // Create form data
      const formData = new FormData();
      formData.append('audio', wavBlob, 'recording.wav');
      
      // Send to backend
      const response = await fetch('http://localhost:8000/api/v1/audio/transcribe', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success && result.text) {
        setTranscriptions(prev => [...prev, result.text]);
        
        // Also send to agent if there's text
        try {
          const agentResponse = await fetch('http://localhost:8000/api/v1/agent/chat', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              message: result.text,
              categories: ['github', 'utility'],
              model: 'gpt-oss-120b'
            }),
          });
          
          if (agentResponse.ok) {
            const agentResult = await agentResponse.json();
            if (agentResult.response) {
              setTranscriptions(prev => [...prev, `AI: ${agentResult.response}`]);
            }
          }
        } catch (agentError) {
          console.error('Agent error:', agentError);
        }
      }
    } catch (error) {
      console.error('Transcription error:', error);
    } finally {
      setIsProcessing(false);
    }
  }, []);
  
  // Start recording
  const startRecording = useCallback(async () => {
    try {
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      // Set up audio context
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      audioContextRef.current = new AudioContextClass({ sampleRate: 16000 });
      
      const source = audioContextRef.current.createMediaStreamSource(stream);
      
      // Use ScriptProcessor to capture audio
      processorRef.current = audioContextRef.current.createScriptProcessor(4096, 1, 1);
      
      processorRef.current.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        audioBufferRef.current.push(new Float32Array(inputData));
      };
      
      source.connect(processorRef.current);
      processorRef.current.connect(audioContextRef.current.destination);
      
      setIsRecording(true);
      
      // Set interval to send audio every 15 seconds (continuous recording)
      recordingTimerRef.current = setInterval(() => {
        sendAudioForTranscription();
      }, 15000);
      
    } catch (error) {
      console.error('Error starting recording:', error);
    }
  }, [sendAudioForTranscription]);
  
  // Stop recording
  const stopRecording = useCallback(() => {
    // Clear interval
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
    
    // Stop recording
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    setIsRecording(false);
    
    // Send audio for transcription
    sendAudioForTranscription();
  }, [sendAudioForTranscription]);
  
  // Toggle recording
  const toggleRecording = useCallback(() => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);
  
  // Clear transcriptions
  const clearTranscriptions = useCallback(() => {
    setTranscriptions([]);
  }, []);
  
  return {
    isRecording,
    isProcessing,
    transcriptions,
    toggleRecording,
    clearTranscriptions,
  };
}