"use client";

import { useTranscription } from "@/hooks/use-transcription";
import {
  ConnectionStatus,
  SessionInfo,
  RecordingTitle,
  WaveformVisualizer,
  RecordButton,
  TranscriptionDisplay,
} from "@/components";

export default function Home() {
  const {
    isRecording,
    transcription,
    connectionStatus,
    session,
    waveformData,
    startRecording,
    stopRecording,
    clearTranscription,
    isConnecting,
  } = useTranscription({
    onTranscription: (text) => {
      console.log("New transcription:", text);
    },
    onSessionStart: (sessionId) => {
      console.log("Session started:", sessionId);
    },
    onError: (error) => {
      console.error("Transcription error:", error);
    },
  });

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-8">
      {/* Connection Status */}
      <ConnectionStatus status={connectionStatus} />

      {/* Session Info */}
      <SessionInfo sessionId={session?.id} />

      {/* Title */}
      <RecordingTitle 
        isRecording={isRecording}
        hasTranscription={transcription.length > 0}
        connectionError={connectionStatus === 'error'}
      />

      {/* Waveform Visualization */}
      <WaveformVisualizer 
        data={waveformData}
        isActive={isRecording}
      />

      {/* Record Button */}
      <RecordButton
        isRecording={isRecording}
        isConnecting={isConnecting}
        onClick={toggleRecording}
      />

      {/* Transcription Display */}
      <TranscriptionDisplay
        transcription={transcription}
        isRecording={isRecording}
        onClear={clearTranscription}
      />

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