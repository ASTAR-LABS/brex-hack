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
      <h1 className="text-3xl text-gray-400 font-light">
        What would you like to record?
      </h1>
      {connectionError && (
        <p className="text-red-500 text-sm mt-2">
          Connection error. Please check your backend is running.
        </p>
      )}
    </div>
  );
}