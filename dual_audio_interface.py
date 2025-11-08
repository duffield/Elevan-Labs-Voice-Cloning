"""
Unified audio interface that handles both conversation and background recording.
This prevents the PyAudio conflict from multiple streams accessing the mic simultaneously.
"""

import pyaudio
import threading
import queue
import wave
import os
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface


class DualAudioInterface(DefaultAudioInterface):
    """
    Audio interface that extends ElevenLabs' default interface to also
    capture audio for background recording without opening multiple streams.
    """
    
    def __init__(self, record_to_file=None, output_dir="Audio-Recordings"):
        """
        Initialize the dual audio interface.
        
        Args:
            record_to_file: Filename to save recording (optional)
            output_dir: Directory to save recordings
        """
        super().__init__()
        self.record_to_file = record_to_file
        self.output_dir = output_dir
        self.recording_frames = []
        self.is_recording = False
        self.recording_lock = threading.Lock()
        
        # Create output directory if needed
        if record_to_file and not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def start_recording(self, filename):
        """Start capturing audio to file."""
        with self.recording_lock:
            self.record_to_file = filename
            self.recording_frames = []
            self.is_recording = True
    
    def stop_recording(self):
        """Stop capturing and save the file."""
        with self.recording_lock:
            self.is_recording = False
            frame_count = len(self.recording_frames)
        
        print(f"\n🎙️  Recording stopped. Captured {frame_count} frames")
        
        if self.recording_frames and self.record_to_file:
            return self._save_recording()
        
        print("⚠️  No frames captured during recording")
        return None
    
    def interrupt(self):
        """Immediately interrupt audio playback and clear output queue."""
        # Call parent's interrupt to clear the output queue
        super().interrupt()
        
        # Also try to stop streams immediately if they exist
        try:
            if hasattr(self, 'out_stream') and self.out_stream:
                # Clear any buffered audio
                if hasattr(self, 'output_queue'):
                    # Drain the queue
                    try:
                        import queue
                        while True:
                            self.output_queue.get_nowait()
                    except:
                        pass
        except Exception:
            pass
    
    def _save_recording(self):
        """Save captured audio to file."""
        output_path = os.path.join(self.output_dir, self.record_to_file)
        
        try:
            # Get audio parameters
            audio = pyaudio.PyAudio()
            wf = wave.open(output_path, 'wb')
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)  # ElevenLabs uses 16kHz
            wf.writeframes(b''.join(self.recording_frames))
            wf.close()
            audio.terminate()
            
            return output_path
        except Exception as e:
            print(f"⚠️  Failed to save recording: {str(e)}")
            return None
    
    def _in_callback(self, in_data, frame_count, time_info, status):
        """
        Override the PyAudio input callback to capture audio.
        This is called by PyAudio when audio data is available from the microphone.
        """
        # Capture for recording if active
        if self.is_recording and isinstance(in_data, bytes):
            with self.recording_lock:
                self.recording_frames.append(in_data)
                if len(self.recording_frames) % 50 == 0:  # Print every 50 frames (~3 seconds)
                    duration = self.get_recording_duration()
                    print(f"\r🎙️  Recording: {duration:.1f}s", end='', flush=True)
        
        # Pass to parent's callback to handle conversation
        return super()._in_callback(in_data, frame_count, time_info, status)
    
    def get_recording_duration(self):
        """Get current recording duration in seconds."""
        if not self.recording_frames:
            return 0
        
        # Calculate based on frame count and sample rate
        # Assuming 16kHz, 16-bit mono audio
        bytes_per_sample = 2
        samples_per_second = 16000
        total_bytes = sum(len(frame) for frame in self.recording_frames)
        total_samples = total_bytes / bytes_per_sample
        duration = total_samples / samples_per_second
        
        return duration
