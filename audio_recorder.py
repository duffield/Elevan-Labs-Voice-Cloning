import pyaudio
import wave
import os
import sys
import struct
from datetime import datetime

class AudioRecorder:
    """Records audio from microphone for voice cloning."""
    
    def __init__(self, duration=30, sample_rate=44100, channels=1, chunk=1024, output_dir="Audio-Recordings"):
        """
        Initialize the audio recorder.
        
        Args:
            duration: Recording duration in seconds (default: 30)
            sample_rate: Audio sample rate in Hz (default: 44100)
            channels: Number of audio channels (default: 1 for mono)
            chunk: Audio chunk size for processing (default: 1024)
            output_dir: Directory to save recordings (default: "Audio-Recordings")
        """
        self.duration = duration
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
        self.format = pyaudio.paInt16
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"📁 Created directory: {self.output_dir}")
        
    def _get_audio_level(self, data):
        """Calculate audio level from chunk data."""
        count = len(data) / 2
        format = "%dh" % count
        shorts = struct.unpack(format, data)
        sum_squares = sum([sample**2 for sample in shorts])
        rms = (sum_squares / count) ** 0.5
        # Normalize to 0-20 range for display
        level = min(20, int(rms / 1638))  # 32768 max / 20 bars
        return level
    
    def _display_level_meter(self, level, remaining):
        """Display audio level meter and countdown."""
        bar = "█" * level + "░" * (20 - level)
        sys.stdout.write(f"\r🔴 {remaining:2d}s │{bar}│ ")
        sys.stdout.flush()
    
    def _list_audio_devices(self, audio):
        """List all available audio input devices."""
        print("\n📋 Available audio input devices:")
        info = audio.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        
        default_device = audio.get_default_input_device_info()
        default_index = default_device['index']
        
        for i in range(num_devices):
            device_info = audio.get_device_info_by_host_api_device_index(0, i)
            if device_info.get('maxInputChannels') > 0:
                marker = "✓" if i == default_index else " "
                print(f"  [{marker}] {i}: {device_info.get('name')}")
        
        print(f"\n✅ Using system default: {default_device['name']}\n")
    
    def record(self, output_file="recorded_voice.wav"):
        """
        Record audio from the system default microphone.
        
        Args:
            output_file: Filename to save (will be saved in output_dir)
            
        Returns:
            str: Path to the saved audio file
        """
        # Save to Audio-Recordings folder
        output_path = os.path.join(self.output_dir, output_file)
        
        print("\n" + "="*50)
        print("🎤 VOICE RECORDING")
        print("="*50)
        
        audio = pyaudio.PyAudio()
        
        # Show available devices and which one is being used
        self._list_audio_devices(audio)
        
        print(f"Preparing to record for {self.duration} seconds...")
        print("Please speak clearly into your microphone.")
        print("\nStarting in 3...")
        
        import time
        time.sleep(1)
        print("2...")
        time.sleep(1)
        print("1...")
        time.sleep(1)
        
        # Open stream with system default device
        stream = audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=None,  # Uses system default
            frames_per_buffer=self.chunk
        )
        
        print(f"\n🔴 RECORDING... Speak now!")
        print(f"Time remaining │ Audio Level Bar │\n")
        
        frames = []
        total_chunks = int(self.sample_rate / self.chunk * self.duration)
        
        # Record for specified duration
        for i in range(total_chunks):
            data = stream.read(self.chunk)
            frames.append(data)
            
            # Calculate progress
            elapsed = (i * self.chunk) / self.sample_rate
            remaining = self.duration - int(elapsed)
            
            # Get audio level and display meter
            level = self._get_audio_level(data)
            self._display_level_meter(level, remaining)
        
        # Clear the line and show completion
        sys.stdout.write("\r" + " " * 60 + "\r")
        print("\n✅ Recording complete!")
        
        # Stop and close stream
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        # Save the recorded audio
        wf = wave.open(output_path, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(audio.get_sample_size(self.format))
        wf.setframerate(self.sample_rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        abs_path = os.path.abspath(output_path)
        print(f"💾 Audio saved to: {abs_path}")
        print("="*50 + "\n")
        
        return output_path


if __name__ == "__main__":
    # Test the recorder
    recorder = AudioRecorder(duration=30, output_dir="Audio-Recordings")
    audio_file = recorder.record("test_recording.wav")
    print(f"Test recording saved: {audio_file}")
