"use client";

import { useTranscription } from "@/hooks/use-transcription";
import { ConnectionStatus } from "@/components/connection-status";
import { SessionInfo } from "@/components/session-info";
import { RecordingTitle } from "@/components/recording-title";
import { WaveformVisualizer } from "@/components/waveform-visualizer";
import { RecordButton } from "@/components/record-button";
import { TranscriptionDisplay } from "@/components/transcription-display";
import { IntegrationsModal } from "@/components/IntegrationsModal";
import { ActionsPanel } from "@/components/ActionsPanel";

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
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-gray-900 to-slate-950 text-white relative overflow-hidden">
      {/* Background gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-r from-purple-900/10 via-transparent to-blue-900/10"></div>
      
      {/* Main content container */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen p-8">
        {/* Integrations Modal */}
        <IntegrationsModal />
        
        {/* Actions Panel - Shows AI agent activity */}
        <ActionsPanel />
        
        {/* Status bar - top of screen */}
        <div className="fixed top-0 left-0 right-0 z-50 p-4">
          <div className="flex justify-between items-center max-w-6xl mx-auto">
            <ConnectionStatus status={connectionStatus} />
            <SessionInfo sessionId={session?.id} />
          </div>
        </div>

        {/* Main content area */}
        <div className="flex flex-col items-center justify-center space-y-8 max-w-6xl mx-auto pt-16">
          {/* Title */}
          <RecordingTitle 
            isRecording={isRecording}
            hasTranscription={transcription.length > 0}
            connectionError={connectionStatus === 'error'}
          />

          {/* Transcription Display */}
          <TranscriptionDisplay
            transcription={transcription}
            isRecording={isRecording}
            onClear={clearTranscription}
          />

          {/* Record Button */}
          <div className="flex flex-col items-center space-y-6">
            <RecordButton
              isRecording={isRecording}
              isConnecting={isConnecting}
              onClick={toggleRecording}
            />
            
            {/* Waveform Visualization */}
            <WaveformVisualizer 
              data={waveformData}
              isActive={isRecording}
            />
          </div>
        </div>
      </div>
    </div>
  );
}