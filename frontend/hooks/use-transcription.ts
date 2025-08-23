'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState, useCallback } from 'react';
import { websocketManager, WebSocketStatus, WebSocketMessage } from '@/lib/websocket-manager';

interface UseTranscriptionOptions {
  onTranscription?: (text: string) => void;
  onSessionStart?: (sessionId: string) => void;
  onError?: (error: Error) => void;
}

interface Session {
  id: string;
  startedAt: string;
  status: string;
}

export function useTranscription(options: UseTranscriptionOptions = {}) {
  const queryClient = useQueryClient();
  const [isRecording, setIsRecording] = useState(false);
  const [waveformData, setWaveformData] = useState<number[]>(new Array(40).fill(0));
  
  // Audio references
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const visualizationContextRef = useRef<AudioContext | null>(null);
  const visualizationStreamRef = useRef<MediaStream | null>(null);

  // Initialize WebSocket manager with query client
  useEffect(() => {
    websocketManager.setQueryClient(queryClient);
  }, [queryClient]);

  // Query for WebSocket status
  const { data: connectionStatus = 'idle' } = useQuery<WebSocketStatus>({
    queryKey: ['websocket-status'],
    queryFn: () => websocketManager.getStatus(),
    staleTime: Infinity,
  });

  // Query for transcription data
  const { data: transcription = [] } = useQuery<string[]>({
    queryKey: ['transcription'],
    queryFn: () => [],
    staleTime: Infinity,
  });

  // Query for session data
  const { data: session } = useQuery<Session | null>({
    queryKey: ['session'],
    queryFn: () => null,
    staleTime: Infinity,
  });

  // Mutation for connecting to WebSocket
  const connectMutation = useMutation({
    mutationFn: () => websocketManager.connect(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['websocket-status'] });
    },
    onError: (error) => {
      console.error('Failed to connect:', error);
      options.onError?.(error as Error);
    },
  });

  // Mutation for disconnecting WebSocket
  const disconnectMutation = useMutation({
    mutationFn: () => {
      websocketManager.disconnect();
      return Promise.resolve();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['websocket-status'] });
    },
  });

  // Mutation for clearing transcription
  const clearTranscriptionMutation = useMutation({
    mutationFn: () => {
      queryClient.setQueryData(['transcription'], []);
      return Promise.resolve();
    },
  });

  // Listen to WebSocket messages
  useEffect(() => {
    const unsubscribe = websocketManager.addMessageListener((message: WebSocketMessage) => {
      if ((message.type === 'session_started' || message.type === 'session_resumed') && message.session_id) {
        options.onSessionStart?.(message.session_id);
      } else if (message.type === 'transcription' && message.is_final && message.text) {
        options.onTranscription?.(message.text);
      }
    });

    return unsubscribe;
  }, [options]);

  // Listen to status changes
  useEffect(() => {
    const unsubscribe = websocketManager.addStatusListener((status) => {
      queryClient.setQueryData(['websocket-status'], status);
    });

    return unsubscribe;
  }, [queryClient]);

  // Waveform visualization
  const visualize = useCallback(() => {
    if (!analyserRef.current) return;
    
    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    const draw = () => {
      animationFrameRef.current = requestAnimationFrame(draw);
      
      if (!analyserRef.current) return;
      analyserRef.current.getByteFrequencyData(dataArray);
      
      const bars = 40;
      const barData = [];
      const step = Math.floor(bufferLength / bars);
      
      for (let i = 0; i < bars; i++) {
        const start = i * step;
        const end = start + step;
        const slice = Array.from(dataArray.slice(start, end));
        const avg = slice.reduce((a, b) => a + b, 0) / slice.length;
        barData.push(avg / 255);
      }
      
      setWaveformData(barData);
    };
    
    draw();
  }, []);

  // Start recording
  const startRecording = useCallback(async () => {
    try {
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      visualizationStreamRef.current = stream.clone();

      // Connect to WebSocket if not connected
      if (!websocketManager.isConnected()) {
        await connectMutation.mutateAsync();
      }

      // Set up audio context with 16kHz sample rate for recording
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      try {
        audioContextRef.current = new AudioContextClass({ sampleRate: 16000 });
      } catch (e) {
        // Fallback if 16kHz is not supported
        console.warn('16kHz sample rate not supported, using default:', e);
        audioContextRef.current = new AudioContextClass();
      }
      
      const source = audioContextRef.current.createMediaStreamSource(stream);
      
      // Try to use AudioWorklet if available (better performance)
      if ('audioWorklet' in audioContextRef.current) {
        try {
          await audioContextRef.current.audioWorklet.addModule('/audio-processor.worklet.js');
          const workletNode = new AudioWorkletNode(audioContextRef.current, 'audio-processor');
          
          workletNode.port.onmessage = (event) => {
            if (event.data.audio && websocketManager.isConnected()) {
              websocketManager.send(event.data.audio);
            }
          };
          
          source.connect(workletNode);
          console.log('Using AudioWorklet for audio processing');
        } catch (e) {
          console.warn('AudioWorklet failed, falling back to ScriptProcessor:', e);
          // Fall through to ScriptProcessor
        }
      }
      
      // Fallback to ScriptProcessor if AudioWorklet not available or failed
      if (!('audioWorklet' in audioContextRef.current) || !source.numberOfOutputs) {
        processorRef.current = audioContextRef.current.createScriptProcessor(4096, 1, 1);

        processorRef.current.onaudioprocess = (e) => {
          if (!websocketManager.isConnected()) return;

          const inputData = e.inputBuffer.getChannelData(0);
          const pcmData = new Int16Array(inputData.length);

          // Convert Float32 to Int16 (PCM)
          for (let i = 0; i < inputData.length; i++) {
            pcmData[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768));
          }

          // Send audio data
          websocketManager.send(pcmData.buffer);
        };

        source.connect(processorRef.current);
        processorRef.current.connect(audioContextRef.current.destination);
        console.log('Using ScriptProcessor for audio processing');
      }
      
      // Set up visualization context (separate from recording)
      visualizationContextRef.current = new AudioContextClass();
      analyserRef.current = visualizationContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      
      const vizSource = visualizationContextRef.current.createMediaStreamSource(visualizationStreamRef.current);
      vizSource.connect(analyserRef.current);
      
      visualize();
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      options.onError?.(error as Error);
    }
  }, [connectMutation, options, visualize]);

  // Stop recording
  const stopRecording = useCallback(() => {
    // Send stop command to backend
    if (websocketManager.isConnected()) {
      websocketManager.sendCommand('stop_recording');
      // Disconnect WebSocket after sending stop command
      // The session will be paused on the backend
      setTimeout(() => {
        disconnectMutation.mutate();
      }, 100);
    }
    
    // Stop recording stream
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
    
    // Stop visualization
    if (visualizationStreamRef.current) {
      visualizationStreamRef.current.getTracks().forEach(track => track.stop());
      visualizationStreamRef.current = null;
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (visualizationContextRef.current) {
      visualizationContextRef.current.close();
      visualizationContextRef.current = null;
    }
    
    setWaveformData(new Array(40).fill(0));
    setIsRecording(false);
  }, [disconnectMutation]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      stopRecording();
      if (websocketManager.isConnected()) {
        disconnectMutation.mutate();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    // State
    isRecording,
    transcription,
    connectionStatus,
    session,
    waveformData,
    
    // Actions
    startRecording,
    stopRecording,
    clearTranscription: clearTranscriptionMutation.mutate,
    connect: connectMutation.mutate,
    disconnect: disconnectMutation.mutate,
    
    // Loading states
    isConnecting: connectMutation.isPending,
    isDisconnecting: disconnectMutation.isPending,
  };
}