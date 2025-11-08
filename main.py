#!/usr/bin/env python3
"""
ElevenLabs Voice Clone Conversational AI
Automates: Record Voice → Clone Voice → Start Conversation
"""

import os
import sys
from dotenv import load_dotenv
from audio_recorder import AudioRecorder
from voice_cloner import VoiceCloner
from conversational_agent import ConversationalAgent


def print_header():
    """Print application header."""
    print("\n" + "="*60)
    print("🎙️  ELEVENLABS VOICE CLONE CONVERSATIONAL AI")
    print("="*60)
    print("\nThis application will:")
    print("  1. 🎤 Record your voice (30 seconds)")
    print("  2. 🧬 Clone your voice using ElevenLabs")
    print("  3. 💬 Start a conversation using your cloned voice")
    print("\n" + "="*60 + "\n")


def main():
    """Main application workflow."""
    print_header()
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("ELEVENLABS_API_KEY")
    
    if not api_key:
        print("❌ ERROR: ELEVENLABS_API_KEY not found!")
        print("\nPlease create a .env file with your API key:")
        print("  ELEVENLABS_API_KEY=your_api_key_here")
        print("\nYou can get your API key from: https://elevenlabs.io/app/settings/api-keys")
        sys.exit(1)
    
    print("✅ API key loaded successfully\n")
    
    # Configuration
    audio_dir = "Audio-Recordings"
    audio_filename = "recorded_voice.wav"
    audio_file = os.path.join(audio_dir, audio_filename)
    voice_name = "My_Cloned_Voice"
    
    # Initialize components
    recorder = AudioRecorder(duration=30, output_dir=audio_dir)
    cloner = VoiceCloner(api_key)
    agent_manager = ConversationalAgent(api_key)
    
    voice_id = None
    agent_id = None
    
    try:
        # Step 1: Record audio or use existing
        print("STEP 1/3: Audio preparation")
        
        # Check if audio file already exists
        if os.path.exists(audio_file):
            print(f"\n📁 Found existing audio file: {audio_file}")
            use_existing = input("Use existing (e) or record new (n)? ").strip().lower()
            
            if use_existing == 'e':
                print(f"✅ Using existing audio file: {audio_file}\n")
            else:
                print("🎤 Recording new audio...")
                audio_file = recorder.record(audio_filename)
        else:
            print("🎤 No existing audio found. Recording new audio...")
            audio_file = recorder.record(audio_filename)
        
        # Step 2: Clone voice with timing
        print("STEP 2/3: Cloning your voice")
        voice_id, cloning_duration = cloner.clone_voice(audio_file, voice_name)
        
        print(f"📊 PERFORMANCE METRIC:")
        print(f"   Voice cloning process took: {cloning_duration:.2f} seconds")
        print(f"   The cloned voice is now ready for use!\n")
        
        # Step 3: Create agent and start conversation
        print("STEP 3/3: Setting up conversational AI")
        
        # Configure the agent
        agent_config = {
            "name": "Voice Clone Assistant",
            "first_message": "Hello! I'm now speaking with your cloned voice. How does it sound? What would you like to talk about?",
            "system_prompt": "You are a friendly assistant speaking with the user's cloned voice. Be conversational, engaging, and helpful. Comment on how interesting it is to speak with their own voice if appropriate.",
            "language": "en"
        }
        
        agent_id = agent_manager.create_agent(voice_id, agent_config)
        
        # Start the conversation
        print("🎉 All setup complete! Starting conversation...\n")
        agent_manager.start_conversation(agent_id)
        
        # Conversation ended
        print("\n✅ Application completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Application interrupted by user")
        
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        print("\n" + "="*60)
        print("🧹 CLEANUP")
        print("="*60)
        
        cleanup_choice = input("\nDo you want to delete the cloned voice and agent? (y/n): ").strip().lower()
        
        if cleanup_choice == 'y':
            if voice_id:
                print(f"\n🗑️  Deleting cloned voice (ID: {voice_id})...")
                cloner.delete_voice(voice_id)
            
            if agent_id:
                print(f"🗑️  Deleting conversational agent (ID: {agent_id})...")
                agent_manager.delete_agent(agent_id)
            
            print("✅ Cleanup complete!")
        else:
            print("\n📝 Resources kept. You can use them later:")
            if voice_id:
                print(f"   Voice ID: {voice_id}")
            if agent_id:
                print(f"   Agent ID: {agent_id}")
        
        # Optionally delete the audio file
        if os.path.exists(audio_file):
            delete_audio = input(f"\nDelete recorded audio file ({audio_file})? (y/n): ").strip().lower()
            if delete_audio == 'y':
                os.remove(audio_file)
                print(f"🗑️  Deleted {audio_file}")
        
        print("\n" + "="*60)
        print("👋 Thank you for using ElevenLabs Voice Clone AI!")
        print("="*60 + "\n")


if __name__ == "__main__":
    main()
