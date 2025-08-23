// Simple AudioWorklet for low-latency audio capture
class AudioProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.bufferSize = 4096;
    this.buffer = [];
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || !input[0]) return true;
    
    // Accumulate samples
    for (const sample of input[0]) {
      this.buffer.push(sample);
      
      if (this.buffer.length >= this.bufferSize) {
        // Convert Float32 to Int16 and send
        const pcm = new Int16Array(this.buffer.map(s => 
          Math.max(-32768, Math.min(32767, s * 32768))
        ));
        
        this.port.postMessage({ audio: pcm.buffer }, [pcm.buffer]);
        this.buffer = [];
      }
    }
    return true;
  }
}

registerProcessor('audio-processor', AudioProcessor);