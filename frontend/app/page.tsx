"use client";

import { useTranscription } from "@/hooks/use-transcription";
import { ConnectionStatus } from "@/components/connection-status";
import { SessionInfo } from "@/components/session-info";
import { RecordingTitle } from "@/components/recording-title";
import { WaveformVisualizer } from "@/components/waveform-visualizer";
import { RecordButton } from "@/components/record-button";
import { TranscriptionDisplay } from "@/components/transcription-display";
import { IntegrationsModal } from "@/components/IntegrationsModal";

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
      {/* Integrations Modal */}
      <IntegrationsModal />
      
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

      {/* Transcription Display - Now on top */}
      <TranscriptionDisplay
        transcription={transcription}
        isRecording={isRecording}
        onClear={clearTranscription}
      />

      {/* Record Button - In the middle */}
      <RecordButton
        isRecording={isRecording}
        isConnecting={isConnecting}
        onClick={toggleRecording}
      />

      {/* Waveform Visualization - Now on bottom */}
      <WaveformVisualizer 
        data={waveformData}
        isActive={isRecording}
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