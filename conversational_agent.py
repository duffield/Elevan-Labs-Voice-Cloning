from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation


class ConversationalAgent:
    """Manages ElevenLabs Conversational AI with a cloned voice."""
    
    def __init__(self, api_key):
        """
        Initialize the conversational agent.
        
        Args:
            api_key: ElevenLabs API key
        """
        self.client = ElevenLabs(api_key=api_key)
        self.conversation = None
    
    def create_agent(self, voice_id, agent_config=None):
        """
        Create and configure a conversational AI agent with the cloned voice.
        
        Args:
            voice_id: The ID of the cloned voice to use
            agent_config: Optional configuration dict for the agent
            
        Returns:
            str: Agent ID
        """
        print("\n" + "="*50)
        print("🤖 CONVERSATIONAL AI SETUP")
        print("="*50)
        print(f"\n🎤 Using cloned voice ID: {voice_id}")
        
        # Default agent configuration
        if agent_config is None:
            agent_config = {
                "name": "Voice Clone Assistant",
                "first_message": "Hello! I'm speaking with your cloned voice. How can I help you today?",
                "system_prompt": "You are a helpful assistant speaking with the user's cloned voice. Be friendly, conversational, and helpful.",
                "language": "en"
            }
        
        try:
            # Create agent with the cloned voice
            agent = self.client.conversational_ai.create_agent(
                name=agent_config["name"],
                voice_id=voice_id,
                first_message=agent_config["first_message"],
                prompt={
                    "prompt": agent_config["system_prompt"]
                },
                language=agent_config["language"]
            )
            
            print(f"✅ Agent created successfully!")
            print(f"🆔 Agent ID: {agent.agent_id}")
            print("="*50 + "\n")
            
            return agent.agent_id
            
        except Exception as e:
            print(f"\n❌ Failed to create agent: {str(e)}")
            print("="*50 + "\n")
            raise
    
    def start_conversation(self, agent_id):
        """
        Start a conversation with the configured agent.
        
        Args:
            agent_id: The ID of the agent to converse with
        """
        print("\n" + "="*50)
        print("💬 STARTING CONVERSATION")
        print("="*50)
        print("\nInitializing conversation with your cloned voice...")
        print("The agent will speak using your voice characteristics.")
        print("\n⚠️  Make sure your microphone and speakers are enabled.")
        print("="*50 + "\n")
        
        try:
            # Start the conversation
            self.conversation = Conversation(
                agent_id=agent_id,
                client=self.client,
                # Audio input/output will be handled automatically
                requires_auth=True
            )
            
            print("🟢 Conversation started!")
            print("Speak into your microphone to interact with the agent.")
            print("The agent will respond using your cloned voice.\n")
            
            # Start the conversation session
            self.conversation.start_session()
            
            print("\n" + "="*50)
            print("👋 Conversation ended")
            print("="*50 + "\n")
            
        except Exception as e:
            print(f"\n❌ Conversation error: {str(e)}")
            print("="*50 + "\n")
            raise
    
    def stop_conversation(self):
        """Stop the active conversation."""
        if self.conversation:
            try:
                self.conversation.end_session()
                print("🛑 Conversation stopped")
            except Exception as e:
                print(f"⚠️  Error stopping conversation: {str(e)}")
    
    def delete_agent(self, agent_id):
        """
        Delete a conversational AI agent.
        
        Args:
            agent_id: ID of the agent to delete
        """
        try:
            self.client.conversational_ai.delete_agent(agent_id)
            print(f"🗑️  Agent {agent_id} deleted successfully")
        except Exception as e:
            print(f"⚠️  Failed to delete agent {agent_id}: {str(e)}")


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("ELEVENLABS_API_KEY")
    
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not found in environment variables")
        exit(1)
    
    # Example: List available voices to use with the agent
    from elevenlabs.client import ElevenLabs
    
    client = ElevenLabs(api_key=api_key)
    voices = client.voices.get_all()
    
    print("\n📋 Available voices for conversational AI:")
    for voice in voices.voices:
        print(f"  - {voice.name} (ID: {voice.voice_id})")
