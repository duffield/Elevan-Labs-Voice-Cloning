#!/usr/bin/env python3
"""
Test script to start a conversation with a voice agent using a default ElevenLabs voice.
This bypasses the voice recording and cloning steps.
"""

import os
import sys

# Add parent directory to path to import conversational_agent module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from conversational_agent import ConversationalAgent


def main():
    # Load API key
    load_dotenv()
    api_key = os.getenv("ELEVENLABS_API_KEY")
    
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not found in .env file")
        print("Please add your API key to the .env file")
        exit(1)
    
    print("\n" + "="*50)
    print("🎙️  VOICE AGENT TEST (Default Voice)")
    print("="*50)
    
    # Initialize client to fetch default voices
    client = ElevenLabs(api_key=api_key)
    
    try:
        # Get available voices
        print("\n📋 Fetching available voices...")
        voices = client.voices.get_all()
        
        if not voices.voices or len(voices.voices) == 0:
            print("❌ No voices available in your account")
            exit(1)
        
        # Use the first available voice as default
        default_voice = voices.voices[0]
        print(f"✅ Using default voice: {default_voice.name}")
        print(f"   Voice ID: {default_voice.voice_id}")
        
    except Exception as e:
        print(f"❌ Failed to fetch voices: {str(e)}")
        exit(1)
    
    # Create conversational agent handler
    agent = ConversationalAgent(api_key=api_key)
    
    # List all available agents
    print("\n📋 Listing all available agents...")
    try:
        agents_list = client.conversational_ai.agents.list()
        if hasattr(agents_list, 'agents') and len(agents_list.agents) > 0:
            for a in agents_list.agents:
                print(f"   - {a.name} (ID: {a.agent_id})")
        else:
            print("   No agents found")
    except Exception as e:
        print(f"   ⚠️  Could not list agents: {str(e)}")
    
    agent_id = None
    try:
        # Find existing agent - try ShapeShifter first, then fall back to "New agent"
        agent_name = "ShapeShifter"
        print(f"\n🔍 Looking for '{agent_name}' agent...")
        target_agent = agent.find_agent_by_name(agent_name)
        
        if not target_agent:
            print(f"   ⚠️  '{agent_name}' not found, trying 'New agent'...")
            agent_name = "New agent"
            target_agent = agent.find_agent_by_name(agent_name)
        
        if not target_agent:
            print("❌ No suitable agent found")
            print("Please create an agent named 'ShapeShifter' or rename 'New agent'")
            return
        
        print(f"✅ Found agent: {agent_name} (ID: {target_agent.agent_id})")
        agent_id = target_agent.agent_id
        
        # Update the agent's voice to the default voice
        agent_id = agent.update_agent_voice(
            agent_id=target_agent.agent_id,
            voice_id=default_voice.voice_id
        )
        
        # Start conversation
        print("💬 Starting conversation...")
        print("Press Ctrl+C to end the conversation\n")
        
        agent.start_conversation(agent_id)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        agent.stop_conversation()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    
    print("\n✅ Test completed!")


if __name__ == "__main__":
    main()
