import time
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings


class VoiceCloner:
    """Clones a voice using ElevenLabs Instant Voice Cloning API."""
    
    def __init__(self, api_key):
        """
        Initialize the voice cloner with ElevenLabs API credentials.
        
        Args:
            api_key: ElevenLabs API key
        """
        self.client = ElevenLabs(api_key=api_key)
        
    def clone_voice(self, audio_file_path, voice_name=None, delete_previous=True):
        """
        Clone a voice from an audio file using ElevenLabs Instant Voice Cloning.
        
        Args:
            audio_file_path: Path to the audio file containing the voice sample
            voice_name: Optional name for the cloned voice (defaults to timestamp)
            delete_previous: If True, deletes any existing voice with the same name before cloning
            
        Returns:
            tuple: (voice_id, cloning_duration_seconds)
        """
        if voice_name is None:
            voice_name = f"Cloned_Voice_{int(time.time())}"
        
        print("\n" + "="*50)
        print("🧬 VOICE CLONING")
        print("="*50)
        print(f"\nVoice name: {voice_name}")
        print(f"Audio file: {audio_file_path}")
        
        # Delete previous voice with same name if it exists
        if delete_previous:
            try:
                voices = self.client.voices.get_all()
                for voice in voices.voices:
                    if voice.name == voice_name:
                        print(f"\n🗑️  Deleting previous voice '{voice_name}' (ID: {voice.voice_id})...")
                        self.delete_voice(voice.voice_id)
                        break
            except Exception as e:
                print(f"⚠️  Could not check for previous voice: {str(e)}")
        
        print("\n⏳ Starting voice cloning process...")
        
        start_time = time.time()
        
        try:
            # Use the IVC (Instant Voice Cloning) endpoint
            with open(audio_file_path, 'rb') as audio_file:
                voice = self.client.voices.ivc.create(
                    name=voice_name,
                    files=[audio_file]
                )
            
            end_time = time.time()
            cloning_duration = end_time - start_time
            
            print(f"\n✅ Voice cloning complete!")
            print(f"⏱️  Voice cloning took: {cloning_duration:.2f} seconds")
            print(f"🆔 Voice ID: {voice.voice_id}")
            print("="*50 + "\n")
            
            return voice.voice_id, cloning_duration
            
        except Exception as e:
            end_time = time.time()
            cloning_duration = end_time - start_time
            print(f"\n❌ Voice cloning failed after {cloning_duration:.2f} seconds")
            print(f"Error: {str(e)}")
            print("="*50 + "\n")
            raise
    
    def delete_voice(self, voice_id):
        """
        Delete a cloned voice from ElevenLabs.
        
        Args:
            voice_id: ID of the voice to delete
        """
        try:
            self.client.voices.delete(voice_id)
            print(f"🗑️  Voice {voice_id} deleted successfully")
        except Exception as e:
            print(f"⚠️  Failed to delete voice {voice_id}: {str(e)}")
    
    def list_voices(self):
        """
        List all available voices in the account.
        
        Returns:
            list: List of voice objects
        """
        try:
            voices = self.client.voices.get_all()
            return voices.voices
        except Exception as e:
            print(f"❌ Failed to list voices: {str(e)}")
            return []


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("ELEVENLABS_API_KEY")
    
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not found in environment variables")
        exit(1)
    
    # Test the voice cloner
    cloner = VoiceCloner(api_key)
    
    # List existing voices
    print("\n📋 Existing voices:")
    voices = cloner.list_voices()
    for voice in voices:
        print(f"  - {voice.name} (ID: {voice.voice_id})")
