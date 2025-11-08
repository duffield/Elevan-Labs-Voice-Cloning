#!/usr/bin/env python3
"""
Automated pipeline: Record voice → Clone it → Update ShapeShifter agent → Start conversation
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from audio_recorder import AudioRecorder
from voice_cloner import VoiceCloner
from conversational_agent import ConversationalAgent


def main():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("ELEVENLABS_API_KEY")
    
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not found in environment variables")
        exit(1)
    
    print("\n" + "="*60)
    print("🤖 AUTOMATED VOICE RECORDING & AGENT UPDATE PIPELINE")
    print("="*60)
    print("\nThis will:")
    print("  1. Record your voice (30 seconds)")
    print("  2. Clone the voice using ElevenLabs")
    print("  3. Update the ShapeShifter agent with your cloned voice")
    print("  4. Start a conversation (optional)")
    print("="*60 + "\n")
    
    # Step 1: Record voice
    print("📍 STEP 1: Recording your voice\n")
    recorder = AudioRecorder(duration=30, output_dir="Audio-Recordings")
    
    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_filename = f"recorded_voice_{timestamp}.wav"
    
    try:
        audio_file = recorder.record(audio_filename)
        print(f"✅ Recording saved: {audio_file}\n")
    except Exception as e:
        print(f"❌ Recording failed: {str(e)}")
        exit(1)
    
    # Step 2: Clone voice
    print("\n📍 STEP 2: Cloning your voice\n")
    cloner = VoiceCloner(api_key)
    voice_name = f"Recorded_Voice_{timestamp}"
    
    try:
        voice_id, duration = cloner.clone_voice(
            audio_file_path=audio_file,
            voice_name=voice_name,
            delete_previous=False  # Keep all recordings
        )
        print(f"✅ Voice cloned: {voice_id}\n")
    except Exception as e:
        print(f"❌ Voice cloning failed: {str(e)}")
        exit(1)
    
    # Step 3: Update ShapeShifter agent
    print("\n📍 STEP 3: Updating ShapeShifter agent\n")
    agent_manager = ConversationalAgent(api_key)
    
    # Find ShapeShifter agent
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
    
    print(f"✅ Found ShapeShifter: {shapeshifter.agent_id}")
    
    try:
        agent_manager.update_agent_voice(
            agent_id=shapeshifter.agent_id,
            voice_id=voice_id
        )
        print(f"✅ ShapeShifter updated with your cloned voice!\n")
    except Exception as e:
        print(f"❌ Failed to update agent: {str(e)}")
        exit(1)
    
    # Summary
    print("\n" + "="*60)
    print("✅ PIPELINE COMPLETE!")
    print("="*60)
    print(f"\n📁 Audio file: {audio_file}")
    print(f"🎤 Voice ID: {voice_id}")
    print(f"🤖 Agent ID: {shapeshifter.agent_id}")
    print(f"📝 Voice name: {voice_name}")
    print("="*60 + "\n")
    
    # Step 4: Optional conversation
    response = input("Would you like to start a conversation with ShapeShifter now? (y/n): ")
    
    if response.lower() == 'y':
        try:
            agent_manager.start_conversation(shapeshifter.agent_id)
        except KeyboardInterrupt:
            print("\n👋 Conversation interrupted by user")
        except Exception as e:
            print(f"❌ Conversation error: {str(e)}")
    else:
        print("\n👋 Done! ShapeShifter is ready to use with your voice.")


if __name__ == "__main__":
    main()
