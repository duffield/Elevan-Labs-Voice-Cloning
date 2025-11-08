#!/usr/bin/env python3
"""
GUI-based call control for voice cloning pipeline.
Uses a GUI window with Start Call and Hangup buttons instead of keyboard input.
"""

import os
import sys
import signal
import threading
from datetime import datetime
from dotenv import load_dotenv
from audio_recorder import AudioRecorder
from smart_audio_recorder import SmartAudioRecorder
from voice_cloner import VoiceCloner
from conversational_agent import ConversationalAgent
from call_gui import CallControlGUI
from dual_audio_interface import DualAudioInterface


# CallRecorder class removed - now using DualAudioInterface for unified recording


class VoiceCloneApp:
    """Main application class that coordinates GUI and call logic."""
    
    def __init__(self):
        self.agent_manager = None
        self.cloner = None
        self.shapeshifter = None
        self.selected_voice_id = None
        self.old_voice_id = None
        self.gui = None
        self.conversation_active = threading.Event()
        self.audio_interface = None
        self.audio_filename = None
        
    def setup(self):
        """Initialize API clients and find ShapeShifter agent."""
        # Load environment variables
        load_dotenv()
        api_key = os.getenv("ELEVENLABS_API_KEY")
        
        if not api_key:
            print("❌ ELEVENLABS_API_KEY not found in environment variables")
            sys.exit(1)
        
        print("\n" + "="*60)
        print("🤖 ADAPTIVE VOICE CLONING PIPELINE (GUI Mode)")
        print("="*60)
        print("\nThis will:")
        print("  1. Open a GUI window with call controls")
        print("  2. Start calls with ShapeShifter using the GUI")
        print("  3. Record your voice during the call (background)")
        print("  4. Clone your voice after the call ends")
        print("  5. Update ShapeShifter for the next call")
        print("="*60 + "\n")
        
        # Initialize components
        self.agent_manager = ConversationalAgent(api_key)
        self.cloner = VoiceCloner(api_key)
        
        # Find ShapeShifter agent
        print("🔍 Looking for ShapeShifter agent...")
        self.shapeshifter = self.agent_manager.find_agent_by_name("ShapeShifter")
        
        if not self.shapeshifter:
            print("❌ ShapeShifter agent not found. Available agents:")
            try:
                agents_list = self.agent_manager.client.conversational_ai.agents.list()
                if hasattr(agents_list, 'agents'):
                    for agent in agents_list.agents:
                        print(f"  - {agent.name} (ID: {agent.agent_id})")
            except Exception as e:
                print(f"⚠️  Could not list agents: {str(e)}")
            sys.exit(1)
        
        print(f"✅ Found ShapeShifter: {self.shapeshifter.agent_id}\n")
        
        # Auto-select Voice_01_Clone for GUI mode
        self._auto_select_voice()
    
    def _auto_select_voice(self):
        """Show GUI dialog for voice selection."""
        import tkinter as tk
        from tkinter import messagebox, simpledialog
        
        print("📍 VOICE SELECTION FOR INITIAL CALL\n")
        
        # Create a simple selection dialog
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Get available voices
        try:
            voices = self.cloner.list_voices()
            voice_01 = next((v for v in voices if v.name == "Voice_01_Clone"), None)
            call_voices = [v for v in voices if v.name.startswith("Call_Voice_")]
            call_voices.sort(key=lambda v: v.name, reverse=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load voices: {str(e)}")
            root.destroy()
            sys.exit(1)
        
        # Build options
        options = []
        if voice_01:
            options.append(("Voice_01_Clone (pre-recorded)", lambda: self._use_voice_01_clone()))
        if call_voices:
            options.append((f"Last recorded call: {call_voices[0].name}", lambda: self._use_last_cloned_voice()))
        if not options:
            messagebox.showerror("Error", "No voices found. Please create a voice clone first.")
            root.destroy()
            sys.exit(1)
        
        # Show selection dialog
        dialog_text = "Select voice for the initial call:\n\n"
        for i, (label, _) in enumerate(options, 1):
            dialog_text += f"{i}. {label}\n"
        
        choice = simpledialog.askinteger(
            "Voice Selection",
            dialog_text + "\nEnter your choice (number):",
            minvalue=1,
            maxvalue=len(options),
            parent=root
        )
        
        root.destroy()
        
        if choice is None:
            print("❌ Voice selection cancelled")
            sys.exit(0)
        
        # Execute selected option
        _, action = options[choice - 1]
        if not action():
            print("❌ Failed to select voice")
            sys.exit(1)
        
        # Store the voice ID used for this call
        self.old_voice_id = self.selected_voice_id
        print(f"✅ Voice selected: {self.selected_voice_id}\n")
    
    def _record_and_clone_voice(self):
        """Record new audio and clone it."""
        print("\n📍 Recording your voice for this call...\n")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_filename = f"pre_call_recording_{timestamp}.wav"
        recorder = AudioRecorder(duration=30, output_dir="Audio-Recordings")
        
        try:
            audio_file = recorder.record(audio_filename)
            print(f"✅ Recording complete: {audio_file}\n")
        except Exception as e:
            print(f"❌ Recording failed: {str(e)}")
            return
        
        # Clone the recorded voice
        print("📍 Cloning recorded voice...\n")
        voice_name = f"Temp_Voice_{timestamp}"
        
        try:
            self.selected_voice_id, _ = self.cloner.clone_voice(
                audio_file_path=audio_file,
                voice_name=voice_name,
                delete_previous=False
            )
            print(f"✅ Voice cloned: {self.selected_voice_id}\n")
        except Exception as e:
            print(f"❌ Voice cloning failed: {str(e)}")
            return
        
        # Update agent
        self._update_agent_voice()
    
    def _use_last_cloned_voice(self):
        """Use most recent Call_Voice clone."""
        print("\n📍 Looking for most recent Call_Voice clone...\n")
        
        try:
            voices = self.cloner.list_voices()
            call_voices = [v for v in voices if v.name.startswith("Call_Voice_")]
            
            if not call_voices:
                print("❌ No Call_Voice clones found from previous sessions.")
                return False
            
            # Sort by name (timestamp) to get most recent
            call_voices.sort(key=lambda v: v.name, reverse=True)
            most_recent = call_voices[0]
            
            self.selected_voice_id = most_recent.voice_id
            print(f"✅ Found most recent clone: {most_recent.name}")
            print(f"   Voice ID: {self.selected_voice_id}\n")
            
        except Exception as e:
            print(f"❌ Failed to find voice: {str(e)}")
            return False
        
        # Update agent
        self._update_agent_voice()
        return True
    
    def _use_voice_01_clone(self):
        """Use Voice_01_Clone."""
        print("\n📍 Looking for Voice_01_Clone...\n")
        
        try:
            voices = self.cloner.list_voices()
            voice_01 = next((v for v in voices if v.name == "Voice_01_Clone"), None)
            
            if not voice_01:
                print("❌ Voice_01_Clone not found. Available voices:")
                for voice in voices:
                    print(f"  - {voice.name} (ID: {voice.voice_id})")
                return False
            
            self.selected_voice_id = voice_01.voice_id
            print(f"✅ Found Voice_01_Clone: {self.selected_voice_id}\n")
        except Exception as e:
            print(f"❌ Failed to find voice: {str(e)}")
            return False
        
        # Update agent
        self._update_agent_voice()
        return True
    
    def _use_first_available_voice(self):
        """Use the first available voice as fallback."""
        print("\n📍 Looking for any available voice...\n")
        
        try:
            voices = self.cloner.list_voices()
            
            if not voices:
                print("❌ No voices found in your account.")
                print("Please create a voice clone first.")
                sys.exit(1)
            
            first_voice = voices[0]
            self.selected_voice_id = first_voice.voice_id
            print(f"✅ Using voice: {first_voice.name}")
            print(f"   Voice ID: {self.selected_voice_id}\n")
            
        except Exception as e:
            print(f"❌ Failed to find voice: {str(e)}")
            sys.exit(1)
        
        # Update agent
        self._update_agent_voice()
        return True
    
    def _update_agent_voice(self):
        """Update ShapeShifter agent with selected voice."""
        print("📍 Updating ShapeShifter with selected voice...\n")
        try:
            self.agent_manager.update_agent_voice(
                agent_id=self.shapeshifter.agent_id,
                voice_id=self.selected_voice_id
            )
            print(f"✅ Agent updated!\n")
        except Exception as e:
            print(f"❌ Failed to update agent: {str(e)}")
            sys.exit(1)
    
    def start_call(self):
        """Start the call (triggered by GUI button)."""
        # Generate timestamp for background recording
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.audio_filename = f"call_recording_{timestamp}.wav"
        
        print("\n📍 Starting call with ShapeShifter\n")
        print("🔴 Recording your voice during call")
        print("💡 Click 'Hangup' button to end call\n")
        
        # Create unified audio interface that handles both conversation and recording
        self.audio_interface = DualAudioInterface(
            record_to_file=self.audio_filename,
            output_dir="Audio-Recordings",
            gui=self.gui
        )
        self.audio_interface.start_recording(self.audio_filename)
        
        # Update GUI status
        if self.gui:
            self.gui.update_status("Starting call...", "blue")
        
        # Set conversation active flag
        self.conversation_active.set()
        
        # Start conversation with custom audio interface
        try:
            print("🔧 DEBUG: About to start conversation...")
            print(f"🔧 DEBUG: Agent ID: {self.shapeshifter.agent_id}")
            print(f"🔧 DEBUG: Audio interface: {type(self.audio_interface).__name__}")
            print(f"🔧 DEBUG: Recording active: {self.audio_interface.is_recording}")
            
            self.agent_manager.start_conversation(
                self.shapeshifter.agent_id,
                audio_interface=self.audio_interface
            )
            print("🔧 DEBUG: Conversation returned normally")
        except KeyboardInterrupt:
            print("\n⚠️  Keyboard interrupt received")
        except Exception as e:
            print(f"\n❌ Call error: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            print("🔧 DEBUG: In finally block")
            self.conversation_active.clear()
            self.gui.call_ended()
            self._process_recording()
    
    def hangup_call(self):
        """End the call (triggered by GUI button)."""
        print("\n📞 Hangup signal received...")
        print("🔧 DEBUG: Calling stop_conversation()")
        self.agent_manager.stop_conversation()
        print("🔧 DEBUG: stop_conversation() returned")
        self.conversation_active.clear()
        print("🔧 DEBUG: Conversation active flag cleared")
    
    def _process_recording(self):
        """Process recording after call ends."""
        print("\n📍 Call ended, saving recording...\n")
        
        # Stop recording and save file
        if self.audio_interface:
            # Get speech duration before stopping
            speech_seconds = self.audio_interface.speech_seconds
            target_duration = self.audio_interface.target_duration
            
            audio_file = self.audio_interface.stop_recording()
        else:
            audio_file = None
            speech_seconds = 0
            target_duration = 20
        
        if not audio_file:
            print("❌ Recording failed or no audio captured")
            return
        
        # Check if we have enough speech (at least 50% of target)
        min_required = target_duration * 0.5
        percentage = (speech_seconds / target_duration) * 100
        
        print(f"✅ Recording saved: {audio_file}")
        print(f"📊 Speech detected: {speech_seconds:.1f}s / {target_duration}s ({percentage:.0f}%)\n")
        
        if speech_seconds < min_required:
            print(f"⚠️  INSUFFICIENT SPEECH DETECTED")
            print(f"   Minimum required: {min_required:.1f}s (50% of {target_duration}s)")
            print(f"   You only spoke for: {speech_seconds:.1f}s ({percentage:.0f}%)\n")
            print("🗑️  Deleting audio file (not enough speech for cloning)...")
            
            # Delete the audio file
            try:
                import os
                os.remove(audio_file)
                print("✅ Audio file deleted\n")
            except Exception as e:
                print(f"⚠️  Could not delete audio file: {str(e)}\n")
            
            print("🚫 Voice cloning SKIPPED - agent voice unchanged")
            print("💡 Speak for at least {:.0f} seconds on the next call to clone your voice.\n".format(min_required))
            
            # Update GUI
            if self.gui:
                self.gui.update_status("Not enough speech - voice unchanged", "orange")
            return
        
        # Clone the recorded voice
        print("📍 Cloning your voice from the call\n")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        voice_name = f"Call_Voice_{timestamp}"
        
        try:
            voice_id, duration = self.cloner.clone_voice(
                audio_file_path=audio_file,
                voice_name=voice_name,
                delete_previous=False
            )
            print(f"✅ Voice cloned: {voice_id}\n")
        except Exception as e:
            error_message = str(e)
            if "voice_limit_reached" in error_message:
                print("❌ Voice cloning failed: You have reached your voice limit.")
                print("Please delete an existing voice from your Eleven Labs account.")
            else:
                print(f"❌ Voice cloning failed: {error_message}")
            return
        
        # Update ShapeShifter with new voice
        print("📍 Updating ShapeShifter for next call\n")
        
        try:
            # Update agent with new voice
            self.agent_manager.update_agent_voice(
                agent_id=self.shapeshifter.agent_id,
                voice_id=voice_id
            )
            print(f"✅ ShapeShifter updated with your new voice!\n")
            
            # Delete old voice to free up quota (never delete Voice_01_Clone)
            if self.old_voice_id:
                print(f"🔧 DEBUG: old_voice_id = {self.old_voice_id}")
                try:
                    voices = self.cloner.list_voices()
                    print(f"🔧 DEBUG: Found {len(voices)} total voices")
                    
                    old_voice_name = next(
                        (v.name for v in voices if v.voice_id == self.old_voice_id),
                        None
                    )
                    
                    print(f"🔧 DEBUG: old_voice_name = {old_voice_name}")
                    
                    if not old_voice_name:
                        print(f"⚠️  Old voice ID {self.old_voice_id} not found in voice list\n")
                    elif old_voice_name == "Voice_01_Clone":
                        print(f"ℹ️  Keeping Voice_01_Clone (protected voice)\n")
                    else:
                        print(f"🗑️  Deleting old voice: {self.old_voice_id} ({old_voice_name})...")
                        self.cloner.delete_voice(self.old_voice_id)
                        print(f"✅ Old voice deleted to free up quota\n")
                except Exception as e:
                    print(f"⚠️  Could not delete old voice: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    print()
            else:
                print("🔧 DEBUG: No old_voice_id set, skipping deletion\n")
            
            # Update for next call
            self.old_voice_id = voice_id
            self.selected_voice_id = voice_id
            
        except Exception as e:
            print(f"❌ Failed to update agent: {str(e)}")
        
        # Summary
        print("\n" + "="*60)
        print("✅ CALL COMPLETE - VOICE UPDATED!")
        print("="*60)
        print(f"\n📁 Recorded audio: {audio_file}")
        print(f"🎤 New voice ID: {voice_id}")
        print(f"🤖 Agent ID: {self.shapeshifter.agent_id}")
        print(f"📝 Voice name: {voice_name}")
        print("\n💡 ShapeShifter will use your recorded voice in the next call!")
        print("   Click 'Start Call' in the GUI to make another call.")
        print("="*60 + "\n")
    
    def run(self):
        """Run the application with GUI."""
        self.setup()
        
        # Create GUI
        print("📱 Opening call control GUI...\n")
        self.gui = CallControlGUI(
            on_start_call=self.start_call,
            on_hangup=self.hangup_call
        )
        
        print("✅ GUI opened! Use the window to control calls.")
        print("   Close the GUI window to exit.\n")
        
        # Run GUI (blocking)
        self.gui.run()
        
        # Cleanup on exit
        print("\n👋 GUI closed - cleaning up...")
        self.agent_manager.stop_conversation(verbose=False)
        print("✅ Done!")


def main():
    app = VoiceCloneApp()
    
    # Set up signal handlers for clean shutdown
    def signal_handler(sig, frame):
        print("\n\n⚠️  Signal received - cleaning up...")
        # Stop any active conversation
        if app.agent_manager:
            app.agent_manager.stop_conversation(verbose=False)
        # Close GUI
        if app.gui and not app.gui.closed:
            print("📱 Closing GUI window...")
            try:
                app.gui.destroy()
            except:
                pass
        print("✅ Cleanup complete")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Keyboard interrupt received - cleaning up...")
        # Stop any active conversation
        if app.agent_manager:
            app.agent_manager.stop_conversation(verbose=False)
        # Close GUI
        if app.gui and not app.gui.closed:
            print("📱 Closing GUI window...")
            app.gui.destroy()
        print("✅ Cleanup complete")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        # Close GUI on error
        if app.gui and not app.gui.closed:
            app.gui.destroy()
        raise


if __name__ == "__main__":
    main()
