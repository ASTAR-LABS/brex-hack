"use client";

import { useState, useRef } from "react";
import { Mic, MicOff } from "lucide-react";
import { IntegrationsModal } from "@/components/IntegrationsModal";

export default function Home() {
  const [isRecording, setIsRecording] = useState(false);
  const [transcription, setTranscription] = useState<string[]>([]);
  const [waveformData, setWaveformData] = useState<number[]>(new Array(40).fill(0));
  
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const mockTranscription = [
    "The", "essence", "of", "luxury", "lies", "not", "in", "excess,",
    "but", "in", "the", "perfect", "balance", "of", "simplicity", "and", "sophistication.",
    "Every", "detail", "matters", "when", "crafting", "an", "experience",
    "that", "transcends", "the", "ordinary."
  ];

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      const AudioContextClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      audioContextRef.current = new AudioContextClass();
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      
      setIsRecording(true);
      setTranscription([]);
      visualize();
      startMockStreaming();
    } catch (err) {
      console.error("Error accessing microphone:", err);
    }
  };

  const stopRecording = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    setIsRecording(false);
    setWaveformData(new Array(40).fill(0));
  };

  const visualize = () => {
    if (!analyserRef.current) return;
    
    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    const draw = () => {
      if (!isRecording) return;
      
      animationFrameRef.current = requestAnimationFrame(draw);
      analyserRef.current!.getByteFrequencyData(dataArray);
      
      
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
  };

  const startMockStreaming = () => {
    let wordIndex = 0;
    const streamWords = () => {
      if (wordIndex < mockTranscription.length && isRecording) {
        setTranscription(prev => [...prev, mockTranscription[wordIndex]]);
        wordIndex++;
        setTimeout(streamWords, 150 + Math.random() * 100);
      }
    };
    setTimeout(streamWords, 500);
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-8">
      <IntegrationsModal />
      {/* Title when not recording */}
      {!isRecording && transcription.length === 0 && (
        <div className="mb-16 text-center animate-fade-in">
          <h1 className="text-3xl text-gray-400 font-light">What would you like to record?</h1>
        </div>
      )}

      {/* Waveform Visualization - Only when recording */}
      {isRecording && (
        <div className="w-full max-w-5xl mb-12 h-40 flex items-center justify-center gap-[2px]">
          {waveformData.map((level, i) => (
            <div
              key={i}
              className="flex-1 bg-gradient-to-t from-emerald-500/80 to-blue-500/80 rounded-sm transition-all duration-100"
              style={{
                height: `${Math.max(2, level * 160)}px`,
                opacity: 0.7 + level * 0.3,
              }}
            />
          ))}
        </div>
      )}

      {/* Record Button - Simplified */}
      <button
        onClick={toggleRecording}
        className={`
          relative w-24 h-24 rounded-full border backdrop-blur-sm
          transition-all duration-200
          ${isRecording 
            ? 'bg-red-500/10 border-red-500' 
            : 'bg-gray-900/30 border-gray-700 hover:border-gray-600'
          }
        `}
      >
        {/* Icon */}
        <div className="flex items-center justify-center w-full h-full">
          {isRecording ? (
            <MicOff className="w-8 h-8 text-white" />
          ) : (
            <Mic className="w-8 h-8 text-white" />
          )}
        </div>

        {/* Live indicator */}
        {isRecording && (
          <div className="absolute -top-2 -right-2">
            <div className="flex items-center gap-1.5 bg-black px-2 py-1 rounded-full">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              <span className="text-[10px] text-red-500 font-medium tracking-wider">LIVE</span>
            </div>
          </div>
        )}
      </button>

      {/* Transcription Display */}
      <div className="w-full max-w-4xl mt-12 min-h-[200px]">
        {(isRecording || transcription.length > 0) && (
          <div className="bg-gray-900/30 border border-gray-800 rounded-2xl p-8 backdrop-blur-sm">
            <p className="text-lg leading-relaxed text-gray-300">
              {transcription.map((word, i) => (
                <span
                  key={i}
                  className="inline-block mr-2 animate-fade-in"
                  style={{
                    animationDelay: `${i * 50}ms`,
                    opacity: 0,
                    animationFillMode: 'forwards',
                  }}
                >
                  {word}
                </span>
              ))}
              {isRecording && transcription.length > 0 && (
                <span className="inline-block w-0.5 h-5 bg-gray-500 animate-pulse ml-1" />
              )}
            </p>
          </div>
        )}
      </div>

      <style jsx>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-fade-in {
          animation: fade-in 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}