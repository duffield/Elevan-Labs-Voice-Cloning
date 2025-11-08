#!/usr/bin/env python3
"""
Test script to verify conversational agent works with existing cloned voice.
Skips the recording and cloning steps.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from conversational_agent import ConversationalAgent

def main():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("ELEVENLABS_API_KEY")
    
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not found in environment variables")
        return
    
    print("\n" + "="*50)
    print("🧪 TESTING CONVERSATIONAL AGENT")
    print("="*50)
    
    # Use the most recent cloned voice (you can change this)
    voice_id = "xfhtoCKFojpqz1rhAb4P"  # Kyle Duffield
    voice_name = "Kyle Duffield"
    
    print(f"\nUsing existing voice: {voice_name}")
    print(f"Voice ID: {voice_id}")
    
    try:
        # Initialize the conversational agent
        agent = ConversationalAgent(api_key)
        
        # Create agent with the cloned voice
        agent_config = {
            "name": f"Test Agent with {voice_name}",
            "first_message": "Hello! This is a test of the conversational agent. How are you doing today?",
            "system_prompt": "You are a friendly conversational AI assistant. Keep responses concise and natural.",
            "language": "en"
        }
        
        agent_id = agent.create_agent(
            voice_id=voice_id,
            agent_config=agent_config
        )
        
        if agent_id:
            print(f"\n✅ Agent created successfully!")
            print(f"🆔 Agent ID: {agent_id}")
            
            # Start conversation
            print("\n🎤 Starting conversation...")
            print("💡 Speak naturally. Press Ctrl+C to end the conversation.\n")
            
            agent.start_conversation(agent_id)
        else:
            print("\n❌ Failed to create agent")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Conversation ended by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        if hasattr(e, '__dict__'):
            print(f"Exception details: {e.__dict__}")
    finally:
        # Cleanup
        print("\n" + "="*50)
        print("🧹 CLEANUP")
        print("="*50)
        
        if 'agent' in locals() and hasattr(agent, 'agent_id') and agent.agent_id:
            delete = input(f"\nDelete agent {agent.agent_id}? (y/n): ").lower().strip()
            if delete == 'y':
                try:
                    agent.client.conversational_ai.delete_agent(agent.agent_id)
                    print(f"🗑️  Agent deleted successfully")
                except Exception as e:
                    print(f"⚠️  Failed to delete agent: {str(e)}")
            else:
                print(f"✅ Agent kept: {agent.agent_id}")

if __name__ == "__main__":
    main()
