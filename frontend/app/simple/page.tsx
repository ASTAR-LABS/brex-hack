'use client';

import { useSimpleRecording } from '@/hooks/use-simple-recording';

export default function SimplePage() {
  const { isRecording, isProcessing, transcriptions, toggleRecording, clearTranscriptions } = useSimpleRecording();

  return (
    <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-8">
      <h1 className="text-5xl font-bold mb-12">
        {isRecording ? 'Listening...' : 'Press to speak'}
      </h1>
      
      {/* Record Button */}
      <button
        onClick={toggleRecording}
        disabled={isProcessing}
        className={`w-32 h-32 rounded-full flex items-center justify-center text-6xl transition-all ${
          isRecording 
            ? 'bg-red-600 hover:bg-red-700 animate-pulse' 
            : 'bg-blue-600 hover:bg-blue-700'
        } ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        {isRecording ? '⏹' : '🎤'}
      </button>
      
      
      {/* Transcriptions */}
      {transcriptions.length > 0 && (
        <div className="mt-8 w-full max-w-2xl">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-semibold">Transcriptions</h2>
            <button
              onClick={clearTranscriptions}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded"
            >
              Clear
            </button>
          </div>
          <div className="space-y-2">
            {transcriptions.map((text, index) => (
              <div
                key={index}
                className={`p-4 rounded ${
                  text.startsWith('AI:') 
                    ? 'bg-blue-900 border-l-4 border-blue-500' 
                    : 'bg-gray-800'
                }`}
              >
                {text}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}