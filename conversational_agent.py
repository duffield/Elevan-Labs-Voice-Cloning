from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface


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
            # Try to create agent - check if there's an existing one first
            try:
                agents_list = self.client.conversational_ai.agents.list()
                if hasattr(agents_list, 'agents') and len(agents_list.agents) > 0:
                    # Use the first existing agent and update it
                    existing_agent = agents_list.agents[0]
                    print(f"\nℹ️  Found existing agent: {existing_agent.name} (ID: {existing_agent.agent_id})")
                    print(f"   Updating it with your cloned voice...")
                    
                    # Update the agent with new voice
                    conversation_config = {
                        "agent": {
                            "prompt": agent_config["system_prompt"],
                            "first_message": agent_config["first_message"],
                            "language": agent_config["language"]
                        },
                        "tts": {
                            "voice_id": voice_id
                        }
                    }
                    
                    self.client.conversational_ai.agents.update(
                        agent_id=existing_agent.agent_id,
                        name=agent_config["name"],
                        conversation_config=conversation_config
                    )
                    
                    agent_id = existing_agent.agent_id
                else:
                    raise Exception("No existing agents found")
            except Exception as list_err:
                print(f"   Could not use existing agent: {str(list_err)}")
                print(f"   Attempting to create new agent...")
                
                # Create conversational config with agent settings using dict
                conversation_config = {
                    "agent": {
                        "prompt": agent_config["system_prompt"],
                        "first_message": agent_config["first_message"],
                        "language": agent_config["language"]
                    },
                    "tts": {
                        "voice_id": voice_id
                    }
                }
                
                # Create agent with the cloned voice
                agent = self.client.conversational_ai.agents.create(
                    name=agent_config["name"],
                    conversation_config=conversation_config
                )
                agent_id = agent.agent_id
            
            print(f"✅ Agent ready!")
            print(f"🆔 Agent ID: {agent_id}")
            print("="*50 + "\n")
            
            return agent_id
            
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
            # Create audio interface for microphone and speakers
            audio_interface = DefaultAudioInterface()
            
            # Start the conversation
            self.conversation = Conversation(
                agent_id=agent_id,
                client=self.client,
                audio_interface=audio_interface,
                requires_auth=True
            )
            
            print("🟢 Conversation started!")
            print("Speak into your microphone to interact with the agent.")
            print("The agent will respond using your cloned voice.")
            print("💡 Press Ctrl+C to end the conversation.\n")
            
            # Start the conversation session (blocking call)
            try:
                self.conversation.start_session()
            except KeyboardInterrupt:
                print("\n⚠️  Interrupting conversation...")
                self.conversation.end_session()
            
            print("\n" + "="*50)
            print("👋 Conversation ended")
            print("="*50 + "\n")
            
        except Exception as e:
            print(f"\n❌ Conversation error: {str(e)}")
            print("="*50 + "\n")
            raise
    
    def stop_conversation(self, verbose=True):
        """Stop the active conversation.
        
        Args:
            verbose: If True, print status messages. If False, stop silently.
        """
        if self.conversation:
            try:
                if verbose:
                    print("\n📞 Ending conversation session...")
                self.conversation.end_session()
                self.conversation = None
                if verbose:
                    print("🛑 Conversation stopped")
            except Exception as e:
                if verbose:
                    print(f"⚠️  Error stopping conversation: {str(e)}")
                # Force clear the conversation object
                self.conversation = None
    
    def find_agent_by_name(self, agent_name):
        """
        Find an agent by name.
        
        Args:
            agent_name: Name of the agent to find
            
        Returns:
            Agent object if found, None otherwise
        """
        try:
            agents_list = self.client.conversational_ai.agents.list()
            if hasattr(agents_list, 'agents'):
                for agent in agents_list.agents:
                    if agent.name == agent_name:
                        return agent
            return None
        except Exception as e:
            print(f"⚠️  Error finding agent: {str(e)}")
            return None
    
    def update_agent_voice(self, agent_id, voice_id, agent_config=None):
        """
        Update an existing agent's voice.
        
        Args:
            agent_id: The ID of the agent to update
            voice_id: The new voice ID to use
            agent_config: Optional configuration dict for the agent
            
        Returns:
            str: Agent ID
        """
        print(f"\n🔄 Updating agent {agent_id} with voice ID: {voice_id}")
        
        try:
            # Build conversation config
            conversation_config = {
                "tts": {
                    "voice_id": voice_id
                }
            }
            
            # Add agent configuration if provided
            if agent_config:
                conversation_config["agent"] = {
                    "prompt": agent_config.get("system_prompt", ""),
                    "first_message": agent_config.get("first_message", ""),
                    "language": agent_config.get("language", "en")
                }
            
            # Update the agent
            self.client.conversational_ai.agents.update(
                agent_id=agent_id,
                conversation_config=conversation_config
            )
            
            print(f"✅ Agent voice updated successfully!")
            return agent_id
            
        except Exception as e:
            print(f"❌ Failed to update agent: {str(e)}")
            raise
    
    def delete_agent(self, agent_id):
        """
        Delete a conversational AI agent.
        
        Args:
            agent_id: ID of the agent to delete
        """
        try:
            self.client.conversational_ai.agents.delete(agent_id)
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
