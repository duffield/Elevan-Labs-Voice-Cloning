#!/usr/bin/env python3
"""
Start a call → Record user's voice during call → Clone voice → Update agent for next call
"""

import os
import sys
import threading
from datetime import datetime
from dotenv import load_dotenv
from audio_recorder import AudioRecorder
from smart_audio_recorder import SmartAudioRecorder
from voice_cloner import VoiceCloner
from conversational_agent import ConversationalAgent


class CallRecorder:
    """Records audio during an active conversation using voice activity detection."""
    
    def __init__(self, target_duration=20, output_dir="Audio-Recordings"):
        self.target_duration = target_duration
        self.output_dir = output_dir
        self.recorder = SmartAudioRecorder(target_duration=target_duration, output_dir=output_dir)
        self.recording_thread = None
        self.audio_file = None
        
    def start_recording(self, filename):
        """Start recording in a separate thread."""
        def record():
            try:
                print(f"\n🔴 Smart recording started (target: {self.target_duration}s of speech)")
                self.audio_file = self.recorder.record(filename, max_total_time=120)
            except Exception as e:
                print(f"\n⚠️  Recording error: {str(e)}")
                self.audio_file = None
        
        self.recording_thread = threading.Thread(target=record, daemon=True)
        self.recording_thread.start()
    
    def wait_for_recording(self):
        """Wait for recording to complete."""
        if self.recording_thread:
            self.recording_thread.join()
        return self.audio_file


def main():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("ELEVENLABS_API_KEY")
    
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not found in environment variables")
        exit(1)
    
    print("\n" + "="*60)
    print("🤖 ADAPTIVE VOICE CLONING PIPELINE")
    print("="*60)
    print("\nThis will:")
    print("  1. Start a call with ShapeShifter")
    print("  2. Record your voice during the call (background)")
    print("  3. Clone your voice after the call ends")
    print("  4. Update ShapeShifter for the next call")
    print("="*60 + "\n")
    
    # Initialize components
    agent_manager = ConversationalAgent(api_key)
    cloner = VoiceCloner(api_key)
    voice_name = None  # Initialize voice_name to None
    
    # Find ShapeShifter agent
    print("🔍 Looking for ShapeShifter agent...")
    shapeshifter = agent_manager.find_agent_by_name("ShapeShifter")
    
    if not shapeshifter:
        print("❌ ShapeShifter agent not found. Available agents:")
        try:
            agents_list = agent_manager.client.conversational_ai.agents.list()
            if hasattr(agents_list, 'agents'):
                for agent in agents_list.agents:
                    print(f"  - {agent.name} (ID: {agent.agent_id})")
        except Exception as e:
            print(f"⚠️  Could not list agents: {str(e)}")
        exit(1)
    
    print(f"✅ Found ShapeShifter: {shapeshifter.agent_id}\n")
    
    # Get current voice ID before starting
    print("🔍 Getting current agent configuration...")
    try:
        current_agent = agent_manager.client.conversational_ai.agents.get(shapeshifter.agent_id)
        current_voice_id = None
        if hasattr(current_agent, 'conversation_config'):
            config = current_agent.conversation_config
            if isinstance(config, dict) and 'tts' in config:
                current_voice_id = config['tts'].get('voice_id')
            elif hasattr(config, 'tts'):
                current_voice_id = getattr(config.tts, 'voice_id', None)
        
        if current_voice_id:
            print(f"✅ Current voice ID: {current_voice_id}\n")
        else:
            print("⚠️  Could not determine current voice ID\n")
    except Exception as e:
        print(f"⚠️  Could not get current voice: {str(e)}\n")
        current_voice_id = None
    
    # Voice selection for testing
    # Track last cloned voice from this session
    last_session_voice_id = None
    selected_voice_id = None
    
    while selected_voice_id is None:
        print("📍 SELECT VOICE FOR THIS CALL\n")
        print("Choose which voice to use for the current call:")
        print("  1. Record new audio now (30s)")
        print("  2. Use last recorded audio from session")
        print("  3. Use Voice_01_Clone (pre-recorded)")
        
        voice_choice = input("\nEnter choice (1, 2, or 3): ").strip()
        
        if voice_choice == "1":
            # Record new voice first
            print("\n📍 Recording your voice for this call...\n")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"pre_call_recording_{timestamp}.wav"
            recorder = AudioRecorder(duration=30, output_dir="Audio-Recordings")
            
            try:
                audio_file = recorder.record(audio_filename)
                print(f"✅ Recording complete: {audio_file}\n")
            except Exception as e:
                print(f"❌ Recording failed: {str(e)}")
                exit(1)
            
            # Clone the recorded voice
            print("📍 Cloning recorded voice...\n")
            voice_name = f"Temp_Voice_{timestamp}"
            
            try:
                selected_voice_id, _ = cloner.clone_voice(
                    audio_file_path=audio_file,
                    voice_name=voice_name,
                    delete_previous=False
                )
                print(f"✅ Voice cloned: {selected_voice_id}\n")
                last_session_voice_id = selected_voice_id  # Track for option 2
            except Exception as e:
                print(f"❌ Voice cloning failed: {str(e)}")
                exit(1)
            
            # Update agent with this voice
            print("📍 Updating ShapeShifter with recorded voice...\n")
            try:
                agent_manager.update_agent_voice(
                    agent_id=shapeshifter.agent_id,
                    voice_id=selected_voice_id
                )
                print(f"✅ Agent updated!\n")
            except Exception as e:
                print(f"❌ Failed to update agent: {str(e)}")
                exit(1)
    
        elif voice_choice == "2":
            # Use most recent Call_Voice clone from previous session
            print("\n📍 Looking for most recent Call_Voice clone...\n")
            
            try:
                voices = cloner.list_voices()
                call_voices = []
                
                # Find all Call_Voice_* clones
                for voice in voices:
                    if voice.name.startswith("Call_Voice_"):
                        call_voices.append(voice)
                
                if not call_voices:
                    print("❌ No Call_Voice clones found from previous sessions.")
                    print("Please choose option 1 or 3.\n")
                    continue
                
                # Sort by name (timestamp) to get most recent
                call_voices.sort(key=lambda v: v.name, reverse=True)
                most_recent = call_voices[0]
                
                selected_voice_id = most_recent.voice_id
                print(f"✅ Found most recent clone: {most_recent.name}")
                print(f"   Voice ID: {selected_voice_id}\n")
                
            except Exception as e:
                print(f"❌ Failed to find voice: {str(e)}")
                print("Please choose option 1 or 3.\n")
                continue
            
            # Update agent with this voice
            print("📍 Updating ShapeShifter with most recent clone...\n")
            try:
                agent_manager.update_agent_voice(
                    agent_id=shapeshifter.agent_id,
                    voice_id=selected_voice_id
                )
                print(f"✅ Agent updated!\n")
            except Exception as e:
                print(f"❌ Failed to update agent: {str(e)}")
                exit(1)
        
        elif voice_choice == "3":
            # Use Voice_01_Clone
            print("\n📍 Looking for Voice_01_Clone...\n")
            
            try:
                voices = cloner.list_voices()
                voice_01 = None
                for voice in voices:
                    if voice.name == "Voice_01_Clone":
                        voice_01 = voice
                        break
                
                if not voice_01:
                    print("❌ Voice_01_Clone not found. Available voices:")
                    for voice in voices:
                        print(f"  - {voice.name} (ID: {voice.voice_id})")
                    exit(1)
                
                selected_voice_id = voice_01.voice_id
                print(f"✅ Found Voice_01_Clone: {selected_voice_id}\n")
            except Exception as e:
                print(f"❌ Failed to find voice: {str(e)}")
                exit(1)
            
            # Update agent with Voice_01_Clone
            print("📍 Updating ShapeShifter with Voice_01_Clone...\n")
            try:
                agent_manager.update_agent_voice(
                    agent_id=shapeshifter.agent_id,
                    voice_id=selected_voice_id
                )
                print(f"✅ Agent updated!\n")
            except Exception as e:
                print(f"❌ Failed to update agent: {str(e)}")
                exit(1)
        
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.\n")
            continue
    
    # Store the voice ID used for this call (will be replaced after call)
    old_voice_id = selected_voice_id
    
    # Generate timestamp for background recording
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_filename = f"call_recording_{timestamp}.wav"
    
    # Create call recorder with smart recording (20s of actual speech)
    call_recorder = CallRecorder(target_duration=20, output_dir="Audio-Recordings")
    
    # Step 1: Start call and recording
    print("📍 STEP 1: Starting call with ShapeShifter\n")
    print("⚠️  The call will start, and your voice will be recorded in background.")
    print("    Speak naturally during the conversation.\n")
    
    input("Press Enter to start the call...")
    
    # Start recording in background
    call_recorder.start_recording(audio_filename)
    
    # Start conversation in a separate thread so we can monitor for hangup
    conversation_active = threading.Event()
    conversation_active.set()
    
    # Create hangup flag file path
    hangup_flag = "/tmp/elevenlabs_hangup.flag"
    if os.path.exists(hangup_flag):
        os.remove(hangup_flag)
    
    def run_conversation():
        try:
            agent_manager.start_conversation(shapeshifter.agent_id)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"\n❌ Call error: {str(e)}")
        finally:
            conversation_active.clear()
    
    def monitor_hangup():
        """Monitor for hangup signal via flag file or keyboard."""
        print("\n💡 Press Enter to hang up the call (or create /tmp/elevenlabs_hangup.flag)\n")
        while conversation_active.is_set():
            # Check for keyboard input
            import select
            import sys
            if sys.platform != 'win32':
                ready, _, _ = select.select([sys.stdin], [], [], 0.5)
                if ready:
                    sys.stdin.readline()
                    print("\n📞 Hangup signal received...")
                    break
            
            # Check for flag file
            if os.path.exists(hangup_flag):
                print("\n📞 Hangup flag detected...")
                os.remove(hangup_flag)
                break
            
            import time
            time.sleep(0.1)
        
        # Send hangup signal
        if conversation_active.is_set():
            print("Ending conversation...")
            agent_manager.stop_conversation()
    
    conversation_thread = threading.Thread(target=run_conversation, daemon=False)
    monitor_thread = threading.Thread(target=monitor_hangup, daemon=True)
    
    conversation_thread.start()
    monitor_thread.start()
    
    # Wait for conversation to end
    try:
        conversation_thread.join()
    except KeyboardInterrupt:
        print("\n⚠️  Call interrupted by Ctrl+C")
        agent_manager.stop_conversation()
        conversation_thread.join(timeout=5)
    finally:
        conversation_active.clear()
    
    print("\n📍 STEP 2: Call ended, waiting for recording to complete...\n")
    
    # Wait for recording to finish
    audio_file = call_recorder.wait_for_recording()
    
    if not audio_file:
        print("❌ Recording failed, cannot proceed with voice cloning")
        exit(1)
    
    print(f"✅ Recording complete: {audio_file}\n")
    
    # Step 2: Clone the recorded voice
    print("📍 STEP 3: Cloning your voice from the call\n")
    voice_name = f"Call_Voice_{timestamp}"
    
    try:
        voice_id, duration = cloner.clone_voice(
            audio_file_path=audio_file,
            voice_name=voice_name,
            delete_previous=False
        )
        print(f"✅ Voice cloned: {voice_id}\n")
        last_session_voice_id = voice_id  # Track for future option 2 selections
    except Exception as e:
        error_message = str(e)
        if "voice_limit_reached" in error_message:
            print("❌ Voice cloning failed: You have reached your voice limit.")
            print("Please delete an existing voice from your Eleven Labs account or upgrade your subscription.")
            exit(1)
        else:
            print(f"❌ Voice cloning failed: {error_message}")
            exit(1)
    
    # Step 3: Update ShapeShifter with new voice, then delete old voice
    print("📍 STEP 4: Updating ShapeShifter for next call\n")
    
    try:
        # First update the agent with new voice
        agent_manager.update_agent_voice(
            agent_id=shapeshifter.agent_id,
            voice_id=voice_id
        )
        print(f"✅ ShapeShifter updated with your new voice!\n")
        
        # Now delete the old voice to free up quota (but never delete Voice_01_Clone)
        if old_voice_id:
            # Check if the old voice is Voice_01_Clone - never delete it
            try:
                voices = cloner.list_voices()
                old_voice_name = None
                for voice in voices:
                    if voice.voice_id == old_voice_id:
                        old_voice_name = voice.name
                        break
                
                if old_voice_name == "Voice_01_Clone":
                    print(f"ℹ️  Keeping Voice_01_Clone (protected voice)\n")
                else:
                    print(f"🗑️  Deleting old voice: {old_voice_id} ({old_voice_name})...")
                    cloner.delete_voice(old_voice_id)
                    print(f"✅ Old voice deleted to free up quota\n")
            except Exception as e:
                print(f"⚠️  Could not delete old voice: {str(e)}\n")
        
    except Exception as e:
        print(f"❌ Failed to update agent: {str(e)}")
        exit(1)
    
    # Summary
    print("\n" + "="*60)
    print("✅ PIPELINE COMPLETE!")
    print("="*60)
    print(f"\n📁 Recorded audio: {audio_file}")
    if 'voice_id' in locals():
        print(f"🎤 New voice ID: {voice_id}")
    else:
        print("🎤 New voice ID: N/A (voice cloning skipped)")
    print(f"🤖 Agent ID: {shapeshifter.agent_id}")
    print(f"📝 Voice name: {voice_name if voice_name else 'N/A'}")
    print("\n💡 ShapeShifter will now use your recorded voice in the next call!")
    print("="*60 + "\n")
    
    # Loop to allow multiple calls with the new voice
    while True:
        response = input("\nPress Enter to start a call with the new voice (or 'q' to quit): ").strip().lower()
        
        if response == 'q':
            print("\n👋 Done! ShapeShifter is ready for the next call with your voice.")
            break
        
        # Start new call
        print("\n🎙️  Starting call with your cloned voice...\n")
        
        # Create hangup flag file path
        hangup_flag = "/tmp/elevenlabs_hangup.flag"
        if os.path.exists(hangup_flag):
            os.remove(hangup_flag)
        
        # Start conversation in a thread
        conversation_active = threading.Event()
        conversation_active.set()
        
        def run_new_conversation():
            try:
                agent_manager.start_conversation(shapeshifter.agent_id)
            except KeyboardInterrupt:
                pass
            except Exception as e:
                print(f"\n❌ Call error: {str(e)}")
            finally:
                conversation_active.clear()
        
        def monitor_hangup():
            """Monitor for hangup signal via flag file or keyboard."""
            print("💡 Press Enter to hang up (or create /tmp/elevenlabs_hangup.flag)\n")
            while conversation_active.is_set():
                # Check for keyboard input
                import select
                import sys
                if sys.platform != 'win32':
                    ready, _, _ = select.select([sys.stdin], [], [], 0.5)
                    if ready:
                        sys.stdin.readline()
                        print("\n📞 Hangup signal received...")
                        break
                
                # Check for flag file
                if os.path.exists(hangup_flag):
                    print("\n📞 Hangup flag detected...")
                    os.remove(hangup_flag)
                    break
                
                import time
                time.sleep(0.1)
            
            # Send hangup signal
            if conversation_active.is_set():
                print("Ending conversation...")
                agent_manager.stop_conversation()
        
        conversation_thread = threading.Thread(target=run_new_conversation, daemon=False)
        monitor_thread = threading.Thread(target=monitor_hangup, daemon=True)
        
        conversation_thread.start()
        monitor_thread.start()
        
        # Wait for conversation to end
        try:
            conversation_thread.join()
        except KeyboardInterrupt:
            print("\n⚠️  Call interrupted by Ctrl+C")
            agent_manager.stop_conversation()
            conversation_thread.join(timeout=5)
        finally:
            conversation_active.clear()
        
        print("\n✅ Call ended")


if __name__ == "__main__":
    main()
