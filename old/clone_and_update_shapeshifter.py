#!/usr/bin/env python3
"""
Clone voice-01.mp3 and update the Shapeshifter agent with the new voice.
"""

import os
from dotenv import load_dotenv
from voice_cloner import VoiceCloner
from conversational_agent import ConversationalAgent


def main():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("ELEVENLABS_API_KEY")
    
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not found in environment variables")
        exit(1)
    
    # Initialize components
    cloner = VoiceCloner(api_key)
    agent_manager = ConversationalAgent(api_key)
    
    # Step 1: Clone voice-01.mp3
    audio_file = "Audio-Recordings/voice-01.mp3"
    voice_name = "Voice_01_Clone"
    
    print(f"\n🎯 Cloning {audio_file}...")
    try:
        voice_id, duration = cloner.clone_voice(
            audio_file_path=audio_file,
            voice_name=voice_name,
            delete_previous=True
        )
        print(f"✅ Voice cloned successfully: {voice_id}")
    except Exception as e:
        print(f"❌ Failed to clone voice: {str(e)}")
        exit(1)
    
    # Step 2: Find Shapeshifter agent
    print(f"\n🔍 Looking for Shapeshifter agent...")
    shapeshifter = agent_manager.find_agent_by_name("ShapeShifter")
    
    if not shapeshifter:
        print("❌ Shapeshifter agent not found. Available agents:")
        try:
            agents_list = agent_manager.client.conversational_ai.agents.list()
            if hasattr(agents_list, 'agents'):
                for agent in agents_list.agents:
                    print(f"  - {agent.name} (ID: {agent.agent_id})")
        except Exception as e:
            print(f"⚠️  Could not list agents: {str(e)}")
        exit(1)
    
    print(f"✅ Found Shapeshifter: {shapeshifter.agent_id}")
    
    # Step 3: Update Shapeshifter's voice
    try:
        agent_manager.update_agent_voice(
            agent_id=shapeshifter.agent_id,
            voice_id=voice_id
        )
        print(f"\n✅ Shapeshifter agent updated with new voice!")
    except Exception as e:
        print(f"❌ Failed to update agent: {str(e)}")
        exit(1)
    
    # Step 4: Start conversation
    print(f"\n🎙️  Ready to start conversation with Shapeshifter")
    response = input("Would you like to start a conversation now? (y/n): ")
    
    if response.lower() == 'y':
        try:
            agent_manager.start_conversation(shapeshifter.agent_id)
        except KeyboardInterrupt:
            print("\n👋 Conversation interrupted by user")
        except Exception as e:
            print(f"❌ Conversation error: {str(e)}")
    else:
        print(f"\n✅ Done! Shapeshifter is ready with voice ID: {voice_id}")
        print(f"   Agent ID: {shapeshifter.agent_id}")


if __name__ == "__main__":
    main()
