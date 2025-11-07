import pyaudio
import wave
import os
from datetime import datetime

class AudioRecorder:
    """Records audio from microphone for voice cloning."""
    
    def __init__(self, duration=30, sample_rate=44100, channels=1, chunk=1024):
        """
        Initialize the audio recorder.
        
        Args:
            duration: Recording duration in seconds (default: 30)
            sample_rate: Audio sample rate in Hz (default: 44100)
            channels: Number of audio channels (default: 1 for mono)
            chunk: Audio chunk size for processing (default: 1024)
        """
        self.duration = duration
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
        self.format = pyaudio.paInt16
        
    def record(self, output_file="recorded_voice.wav"):
        """
        Record audio from the default microphone.
        
        Args:
            output_file: Path to save the recorded audio file
            
        Returns:
            str: Path to the saved audio file
        """
        print("\n" + "="*50)
        print("🎤 VOICE RECORDING")
        print("="*50)
        print(f"\nPreparing to record for {self.duration} seconds...")
        print("Please speak clearly into your microphone.")
        print("\nStarting in 3...")
        
        import time
        time.sleep(1)
        print("2...")
        time.sleep(1)
        print("1...")
        time.sleep(1)
        
        audio = pyaudio.PyAudio()
        
        # Open stream
        stream = audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        print(f"\n🔴 RECORDING NOW... ({self.duration} seconds)")
        print("Speak naturally to capture your voice characteristics.\n")
        
        frames = []
        
        # Record for specified duration
        for i in range(0, int(self.sample_rate / self.chunk * self.duration)):
            data = stream.read(self.chunk)
            frames.append(data)
            
            # Show progress every 5 seconds
            elapsed = (i * self.chunk) / self.sample_rate
            if elapsed % 5 == 0 and elapsed > 0:
                remaining = self.duration - elapsed
                if remaining > 0:
                    print(f"⏱️  {int(remaining)} seconds remaining...")
        
        print("\n✅ Recording complete!")
        
        # Stop and close stream
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        # Save the recorded audio
        wf = wave.open(output_file, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(audio.get_sample_size(self.format))
        wf.setframerate(self.sample_rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        print(f"💾 Audio saved to: {output_file}")
        print("="*50 + "\n")
        
        return output_file


if __name__ == "__main__":
    # Test the recorder
    recorder = AudioRecorder(duration=30)
    audio_file = recorder.record("test_recording.wav")
    print(f"Test recording saved: {audio_file}")
