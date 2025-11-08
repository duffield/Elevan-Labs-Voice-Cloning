"""
Unified audio interface that handles both conversation and background recording.
This prevents the PyAudio conflict from multiple streams accessing the mic simultaneously.
"""

import pyaudio
import threading
import queue
import wave
import os
import sys
import struct
import time
import contextlib
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface


@contextlib.contextmanager
def suppress_stderr():
    """Temporarily suppress stderr to hide PortAudio warnings."""
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    try:
        os.dup2(devnull, 2)
        yield
    finally:
        os.dup2(old_stderr, 2)
        os.close(devnull)
        os.close(old_stderr)


class DualAudioInterface(DefaultAudioInterface):
    """
    Audio interface that extends ElevenLabs' default interface to also
    capture audio for background recording without opening multiple streams.
    """
    
    # Increase output buffer to prevent PortAudio underruns on macOS
    INPUT_FRAMES_PER_BUFFER = 4000   # 250ms @ 16kHz (parent default)
    OUTPUT_FRAMES_PER_BUFFER = 4000  # 250ms @ 16kHz (increased from 1000 to match input)
    
    def __init__(self, record_to_file=None, output_dir="Audio-Recordings", gui=None, target_duration=20):
        """
        Initialize the dual audio interface.
        
        Args:
            record_to_file: Filename to save recording (optional)
            output_dir: Directory to save recordings
            gui: Optional GUI reference for status updates
            target_duration: Target duration of actual speech in seconds (default: 20)
        """
        super().__init__()
        self.record_to_file = record_to_file
        self.output_dir = output_dir
        self.recording_frames = []
        self.speech_frames = []  # Only frames with actual speech
        self.is_recording = False
        self.recording_lock = threading.Lock()
        self.gui = gui
        
        # Voice Activity Detection parameters
        self.target_duration = target_duration
        self.silence_threshold = 500  # RMS threshold for silence
        self.speech_seconds = 0
        self.currently_speaking = False
        self._last_status = None
        self.recording_complete = False
        
        # Debouncing buffers
        self.silence_debounce = 1.5  # Seconds of silence before pausing
        self.silence_buffer = []
        self.silence_buffer_max = int(16000 / 4000 * self.silence_debounce)  # ~1.5 seconds worth of chunks
        
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
    
    
    def _output_thread(self):
        """Override output thread with better error handling for PortAudio issues."""
        error_count = 0
        max_consecutive_errors = 5
        
        while not self.should_stop.is_set():
            try:
                audio = self.output_queue.get(timeout=0.25)
                try:
                    self.out_stream.write(audio)
                    error_count = 0  # Reset on success
                except OSError as e:
                    error_count += 1
                    if error_count >= max_consecutive_errors:
                        print(f"\n⚠️  Audio output error (attempt {error_count}): {e}")
                        print("   Attempting to recover...")
                        try:
                            # Try to recreate the output stream
                            self.out_stream.stop_stream()
                            self.out_stream.close()
                            self.out_stream = self.p.open(
                                format=self.pyaudio.paInt16,
                                channels=1,
                                rate=16000,
                                output=True,
                                frames_per_buffer=self.OUTPUT_FRAMES_PER_BUFFER,
                                start=True,
                            )
                            error_count = 0
                            print("   ✅ Audio output recovered")
                        except Exception as recovery_error:
                            print(f"   ❌ Recovery failed: {recovery_error}")
                            break
            except queue.Empty:
                pass
    
    def interrupt(self):
        """Immediately interrupt audio playback and clear output queue."""
        # First, aggressively clear the output queue to minimize latency
        if hasattr(self, 'output_queue'):
            try:
                import queue
                # Clear queue without blocking
                while not self.output_queue.empty():
                    try:
                        self.output_queue.get_nowait()
                    except queue.Empty:
                        break
            except Exception:
                pass
        
        # Stop and restart output stream to interrupt playback immediately
        # but keep stream alive for conversation
        if hasattr(self, 'out_stream') and self.out_stream:
            try:
                if self.out_stream.is_active():
                    self.out_stream.stop_stream()
                    # Immediately restart it
                    self.out_stream.start_stream()
            except Exception:
                # If restart fails, try to recreate the stream
                try:
                    self.out_stream.close()
                    self.out_stream = self.p.open(
                        format=self.pyaudio.paInt16,
                        channels=1,
                        rate=16000,
                        output=True,
                        frames_per_buffer=self.OUTPUT_FRAMES_PER_BUFFER,
                        start=True,
                    )
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
    
    def _get_audio_level(self, data):
        """Calculate RMS audio level from chunk data."""
        try:
            count = len(data) // 2
            format_str = "%dh" % count
            shorts = struct.unpack(format_str, data)
            sum_squares = sum([sample**2 for sample in shorts])
            rms = (sum_squares / count) ** 0.5
            return rms
        except:
            return 0
    
    def _is_speech(self, data):
        """Determine if audio chunk contains speech based on RMS level."""
        rms = self._get_audio_level(data)
        return rms > self.silence_threshold
    
    def _display_progress(self, speech_seconds, is_speaking):
        """Display recording progress with voice activity indicator."""
        bar_length = 30
        progress = min(1.0, speech_seconds / self.target_duration)
        filled = int(bar_length * progress)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        status = "🔴 RECORDING" if is_speaking else "⏸️  WAITING"
        percentage = int(progress * 100)
        
        status_line = f"{status} - {speech_seconds:.1f}/{self.target_duration}s speech ({percentage}%)"
        
        # Update console with carriage return to overwrite same line
        # Add spaces at end to clear any previous longer text
        sys.stdout.write(f"\r{status_line} │{bar}│" + " " * 10)
        sys.stdout.flush()
        
        # Update GUI if available
        if self.gui:
            gui_status = f"Recording: {speech_seconds:.1f}s / {self.target_duration}s ({percentage}%)"
            color = "red" if is_speaking else "orange"
            self.gui.update_status(gui_status, color)
    
    def _in_callback(self, in_data, frame_count, time_info, status):
        """
        Override the PyAudio input callback to capture audio.
        This is called by PyAudio when audio data is available from the microphone.
        """
        # Capture for recording if active and not yet complete
        if self.is_recording and isinstance(in_data, bytes) and not self.recording_complete:
            with self.recording_lock:
                # Always capture all audio
                self.recording_frames.append(in_data)
                
                # Detect if this is speech
                is_speech = self._is_speech(in_data)
                
                if is_speech:
                    # Add buffered silence (debounce - includes short pauses as speech)
                    if self.silence_buffer and self.currently_speaking:
                        self.speech_frames.extend(self.silence_buffer)
                    self.silence_buffer = []
                    
                    # Count this as speech
                    self.speech_frames.append(in_data)
                    self.speech_seconds = len(self.speech_frames) * len(in_data) / (16000 * 2)  # 16kHz, 16-bit
                    self.currently_speaking = True
                    self._display_progress(self.speech_seconds, True)
                    
                    # Check if we've reached the target
                    if self.speech_seconds >= self.target_duration:
                        self.recording_complete = True
                        print("\n\n✅ Target speech duration reached! Recording complete.")
                        if self.gui:
                            self.gui.update_status(f"Recording complete: {self.speech_seconds:.1f}s", "green")
                else:
                    # Silence detected
                    if self.currently_speaking:
                        # Add to silence buffer (debounce - keeps short pauses)
                        self.silence_buffer.append(in_data)
                        
                        # If silence buffer exceeds debounce threshold, stop counting
                        if len(self.silence_buffer) >= self.silence_buffer_max:
                            self.currently_speaking = False
                            self.silence_buffer = []
                            self._display_progress(self.speech_seconds, False)
                        else:
                            # Still within debounce window - keep displaying as recording
                            self._display_progress(self.speech_seconds, True)
                    else:
                        # Not recording, just show waiting
                        self._display_progress(self.speech_seconds, False)
        
        # Pass to parent's callback to handle conversation
        # Suppress stderr to prevent PortAudio warnings from breaking progress display
        with suppress_stderr():
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
