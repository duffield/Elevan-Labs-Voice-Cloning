#!/usr/bin/env python3
"""
Update an existing ElevenLabs conversational agent with a cloned voice.
"""

import os
from dotenv import load_dotenv
from conversational_agent import ConversationalAgent

def main():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("ELEVENLABS_API_KEY")
    
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not found in .env file")
        return
    
    # Your cloned voice ID from the previous run
    cloned_voice_id = "PlRe3MB6J7FbHUJWlslY"
    
    # Initialize the agent manager
    agent_manager = ConversationalAgent(api_key)
    
    print("\n" + "="*60)
    print("🔄 UPDATE AGENT WITH CLONED VOICE")
    print("="*60)
    
    # List available agents
    try:
        agents_list = agent_manager.client.conversational_ai.agents.list()
        
        if not hasattr(agents_list, 'agents') or len(agents_list.agents) == 0:
            print("\n⚠️  No existing agents found.")
            print("Create an agent first on the ElevenLabs dashboard.")
            return
        
        print(f"\n📋 Found {len(agents_list.agents)} agent(s):\n")
        for i, agent in enumerate(agents_list.agents, 1):
            print(f"  {i}. {agent.name}")
            print(f"     ID: {agent.agent_id}")
            print()
        
        # Select an agent
        choice = input("Enter the number of the agent to update: ").strip()
        
        try:
            agent_index = int(choice) - 1
            if agent_index < 0 or agent_index >= len(agents_list.agents):
                print("❌ Invalid selection")
                return
            
            selected_agent = agents_list.agents[agent_index]
            
            print(f"\n✅ Selected: {selected_agent.name} (ID: {selected_agent.agent_id})")
            print(f"🎤 Cloned voice ID: {cloned_voice_id}")
            
            confirm = input("\nUpdate this agent's voice? (y/n): ").strip().lower()
            
            if confirm != 'y':
                print("❌ Cancelled")
                return
            
            # Update the agent's voice
            agent_manager.update_agent_voice(
                agent_id=selected_agent.agent_id,
                voice_id=cloned_voice_id
            )
            
            print("\n" + "="*60)
            print("✅ AGENT VOICE UPDATED SUCCESSFULLY!")
            print("="*60)
            print(f"\nAgent '{selected_agent.name}' now uses your cloned voice.")
            print(f"Agent ID: {selected_agent.agent_id}")
            print(f"Voice ID: {cloned_voice_id}")
            
            # Ask if user wants to test the conversation
            test = input("\nStart a conversation to test it? (y/n): ").strip().lower()
            
            if test == 'y':
                print("\n🎉 Starting conversation with updated agent...\n")
                agent_manager.start_conversation(selected_agent.agent_id)
            
        except ValueError:
            print("❌ Invalid number entered")
            return
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
