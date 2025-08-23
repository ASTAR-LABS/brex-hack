'use client';

interface WaveformVisualizerProps {
  data: number[];
  isActive: boolean;
}

export function WaveformVisualizer({ data, isActive }: WaveformVisualizerProps) {
  if (!isActive) return null;

  return (
    <div className="w-full max-w-5xl mt-12 h-40 flex items-center justify-center gap-[2px]">
      {data.map((level, i) => (
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
  );
}