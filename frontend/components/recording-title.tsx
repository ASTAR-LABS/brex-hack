'use client';

interface RecordingTitleProps {
  isRecording: boolean;
  hasTranscription: boolean;
  connectionError: boolean;
}

export function RecordingTitle({ isRecording, hasTranscription, connectionError }: RecordingTitleProps) {
  if (isRecording || hasTranscription) return null;

  return (
    <div className="mb-16 text-center animate-fade-in">
      <div className="mb-6">
        <h1 className="text-4xl font-light bg-gradient-to-r from-slate-200 via-white to-slate-200 bg-clip-text text-transparent mb-4">
          Voice Transcription
        </h1>
        <p className="text-lg text-slate-400 font-light">
          Click the button below to start recording
        </p>
      </div>
      {connectionError && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 max-w-md mx-auto">
          <p className="text-red-400 text-sm font-medium">
            Connection error. Please check your backend is running.
          </p>
        </div>
      )}
    </div>
  );
}