import pyaudio
import wave
import os
import sys
import struct
import numpy as np
from datetime import datetime


class SmartAudioRecorder:
    """Records audio only when sound is detected (voice activity detection)."""
    
    def __init__(self, target_duration=20, sample_rate=44100, channels=1, chunk=1024, output_dir="Audio-Recordings"):
        """
        Initialize the smart audio recorder.
        
        Args:
            target_duration: Target duration of actual speech in seconds (default: 20)
            sample_rate: Audio sample rate in Hz (default: 44100)
            channels: Number of audio channels (default: 1 for mono)
            chunk: Audio chunk size for processing (default: 1024)
            output_dir: Directory to save recordings (default: "Audio-Recordings")
        """
        self.target_duration = target_duration
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
        self.format = pyaudio.paInt16
        self.output_dir = output_dir
        
        # Voice Activity Detection parameters
        self.silence_threshold = 500  # RMS threshold for silence (adjustable)
        self.min_speech_chunk = 0.3  # Minimum speech duration to count (seconds)
        self.silence_debounce = 1.5  # Seconds of silence before pausing (debounce)
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"📁 Created directory: {self.output_dir}")
    
    def _get_audio_level(self, data):
        """Calculate RMS audio level from chunk data."""
        count = len(data) // 2
        format_str = "%dh" % count
        shorts = struct.unpack(format_str, data)
        sum_squares = sum([sample**2 for sample in shorts])
        rms = (sum_squares / count) ** 0.5
        return rms
    
    def _is_speech(self, data):
        """Determine if audio chunk contains speech based on RMS level."""
        rms = self._get_audio_level(data)
        return rms > self.silence_threshold
    
    def _display_progress(self, speech_seconds, total_seconds, is_recording, force_update=False):
        """Display recording progress with voice activity indicator."""
        bar_length = 30
        progress = min(1.0, speech_seconds / self.target_duration)
        filled = int(bar_length * progress)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        status = "🔴 RECORDING" if is_recording else "⏸️  WAITING"
        percentage = int(progress * 100)
        
        # Only update if forced or state hasn't been printed yet
        if force_update or not hasattr(self, '_last_status') or self._last_status != status:
            if hasattr(self, '_last_status'):
                print()  # New line when state changes
            print(f"{status} - {speech_seconds:.1f}/{self.target_duration}s speech ({percentage}%)")
            self._last_status = status
        
        # Always update the progress bar on same line
        sys.stdout.write(f"\r│{bar}│ {total_seconds:.0f}s total")
        sys.stdout.flush()
    
    def record(self, output_file="smart_recorded_voice.wav", max_total_time=120, stop_flag=None):
        """
        Record audio, only capturing when speech is detected.
        
        Args:
            output_file: Filename to save (will be saved in output_dir)
            max_total_time: Maximum total recording time in seconds (default: 120)
            
        Returns:
            str: Path to the saved audio file
        """
        output_path = os.path.join(self.output_dir, output_file)
        
        print("\n" + "="*70)
        print("🎤 SMART VOICE RECORDING (Voice Activity Detection)")
        print("="*70)
        print(f"\nTarget speech duration: {self.target_duration} seconds")
        print(f"Maximum total time: {max_total_time} seconds")
        print("\n💡 The recorder will only capture when you're speaking.")
        print("   When you're silent, recording pauses automatically.")
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
            input_device_index=None,
            frames_per_buffer=self.chunk
        )
        
        print(f"\n🎙️  Recording started! Speak naturally...\n")
        
        frames = []
        speech_frames = 0
        total_frames = 0
        target_frames = int(self.sample_rate / self.chunk * self.target_duration)
        max_frames = int(self.sample_rate / self.chunk * max_total_time)
        
        speech_buffer = []
        speech_buffer_duration = int(self.sample_rate / self.chunk * self.min_speech_chunk)
        
        # Debounce buffer for silence
        silence_buffer = []
        silence_buffer_max = int(self.sample_rate / self.chunk * self.silence_debounce)
        
        currently_recording = False
        
        # Initialize actual_speech_seconds for external monitoring
        self.actual_speech_seconds = 0
        
        try:
            while speech_frames < target_frames and total_frames < max_frames:
                # Check if stop was requested
                if stop_flag and stop_flag.is_set():
                    print("\n\n⚠️  Recording stopped by external signal")
                    break
                
                data = stream.read(self.chunk, exception_on_overflow=False)
                total_frames += 1
                
                # Check if this chunk contains speech
                is_speech = self._is_speech(data)
                
                if is_speech:
                    # Add to speech buffer
                    speech_buffer.append(data)
                    
                    # If we were in silence, add buffered silence too (to avoid cutting words)
                    if silence_buffer and currently_recording:
                        speech_buffer.extend(silence_buffer)
                    silence_buffer = []
                    
                    # If buffer is long enough, count it as speech
                    if len(speech_buffer) >= speech_buffer_duration:
                        # Add all buffered frames
                        frames.extend(speech_buffer)
                        speech_frames += len(speech_buffer)
                        speech_buffer = []
                        currently_recording = True
                        
                        # Update display and external counter
                        speech_seconds = (speech_frames * self.chunk) / self.sample_rate
                        self.actual_speech_seconds = speech_seconds
                        total_seconds = (total_frames * self.chunk) / self.sample_rate
                        self._display_progress(speech_seconds, total_seconds, True)
                else:
                    # Silence detected
                    if currently_recording:
                        # Add to silence buffer (debounce)
                        silence_buffer.append(data)
                        
                        # If silence buffer exceeds debounce threshold, stop recording
                        if len(silence_buffer) >= silence_buffer_max:
                            currently_recording = False
                            silence_buffer = []
                            speech_buffer = []
                            
                            # Update display (not recording anymore)
                            speech_seconds = (speech_frames * self.chunk) / self.sample_rate
                            total_seconds = (total_frames * self.chunk) / self.sample_rate
                            self._display_progress(speech_seconds, total_seconds, False)
                        else:
                            # Still within debounce window - keep displaying as recording
                            speech_seconds = (speech_frames * self.chunk) / self.sample_rate
                            total_seconds = (total_frames * self.chunk) / self.sample_rate
                            self._display_progress(speech_seconds, total_seconds, True)
                    else:
                        # Not recording, just reset buffers
                        silence_buffer = []
                        speech_buffer = []
                        
                        # Update display (waiting)
                        speech_seconds = (speech_frames * self.chunk) / self.sample_rate
                        total_seconds = (total_frames * self.chunk) / self.sample_rate
                        self._display_progress(speech_seconds, total_seconds, False)
            
            # Add any remaining buffer
            if speech_buffer:
                frames.extend(speech_buffer)
                speech_frames += len(speech_buffer)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Recording interrupted by user")
        
        # Clear the line and show completion
        sys.stdout.write("\r" + " " * 100 + "\r")
        
        final_speech_seconds = (speech_frames * self.chunk) / self.sample_rate
        final_total_seconds = (total_frames * self.chunk) / self.sample_rate
        
        # Store actual speech duration for external access
        self.actual_speech_seconds = final_speech_seconds
        
        print(f"\n✅ Recording complete!")
        print(f"   Speech captured: {final_speech_seconds:.1f} seconds")
        print(f"   Total time: {final_total_seconds:.1f} seconds")
        if final_total_seconds > 0:
            print(f"   Efficiency: {(final_speech_seconds/final_total_seconds*100):.1f}%")
        
        # Stop and close stream
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        # Save the recorded audio
        if frames:
            wf = wave.open(output_path, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(audio.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            abs_path = os.path.abspath(output_path)
            print(f"💾 Audio saved to: {abs_path}")
            print("="*70 + "\n")
            
            return output_path
        else:
            print("⚠️  No speech detected, no file saved")
            print("="*70 + "\n")
            return None


if __name__ == "__main__":
    # Test the smart recorder
    recorder = SmartAudioRecorder(target_duration=20, output_dir="Audio-Recordings")
    audio_file = recorder.record("test_smart_recording.wav")
    if audio_file:
        print(f"Test recording saved: {audio_file}")
