# ElevenLabs Voice Clone Conversational AI

An automated application that records your voice, clones it using ElevenLabs Instant Voice Cloning, and starts a conversational AI agent that speaks with your cloned voice.

## Features

- 🎤 **Voice Recording**: Automatically records 30 seconds of audio from your microphone
- 🧬 **Voice Cloning**: Uses ElevenLabs Instant Voice Cloning API to create a voice model
- 💬 **Conversational AI**: Engages in natural conversation using your cloned voice
- ⏱️ **Performance Metrics**: Displays voice cloning duration in console
- 🎯 **Fully Automated**: Complete workflow from recording to conversation

## Prerequisites

- Python 3.7 or higher
- ElevenLabs account with Starter Plan or higher
- Microphone and speakers/headphones
- macOS (tested) or Linux (PyAudio support required)

## Installation

1. **Clone or download this repository**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   Note: On macOS, if you encounter issues installing PyAudio, you may need to install PortAudio first:
   ```bash
   brew install portaudio
   pip install pyaudio
   ```

3. **Set up your ElevenLabs API key**:
   - Get your API key from [ElevenLabs Settings](https://elevenlabs.io/app/settings/api-keys)
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your API key:
     ```
     ELEVENLABS_API_KEY=your_actual_api_key_here
     ```

## Usage

Run the main application:

```bash
python main.py
```

The application will guide you through three automated steps:

1. **Recording**: You'll have a 3-second countdown, then record for 30 seconds
2. **Cloning**: Your voice will be cloned (duration displayed in console)
3. **Conversation**: An AI agent will start speaking with your cloned voice

### What to Expect

- Clear console prompts guide you through each step
- Recording shows countdown and progress indicators
- Voice cloning displays elapsed time
- Conversation starts automatically with your cloned voice
- At the end, you can choose to clean up resources

## Project Structure

```
.
├── main.py                  # Main application orchestrator
├── audio_recorder.py        # Voice recording module
├── voice_cloner.py          # ElevenLabs voice cloning integration
├── conversational_agent.py  # Conversational AI agent management
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .env                    # Your API key (not in git)
└── README.md              # This file
```

## API Usage & Limits

This application uses the ElevenLabs API with the following considerations:

- **Voice Cloning**: Instant Voice Cloning is available on Starter plan and above
- **Conversational AI**: Real-time conversational agents require API access
- **Character Limits**: Voice cloning and conversations consume your monthly character quota

Monitor your usage at [ElevenLabs Usage Dashboard](https://elevenlabs.io/app/usage)

## Troubleshooting

### PyAudio Installation Issues

**macOS**:
```bash
brew install portaudio
pip install pyaudio
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

### Microphone Not Working

- Ensure microphone permissions are granted to Terminal/Python
- Check System Preferences → Security & Privacy → Microphone
- Test your microphone with another application first

### API Errors

- Verify your API key is correct in `.env`
- Check your ElevenLabs account quota and plan limits
- Ensure you have an active internet connection

## Cleanup

The application will prompt you after each run to:
- Delete the cloned voice from your ElevenLabs account
- Delete the conversational agent
- Delete the local audio recording file

This helps manage your ElevenLabs resources and local storage.

## Development

Each module can be tested independently:

```bash
# Test audio recording
python audio_recorder.py

# Test voice cloning
python voice_cloner.py

# Test conversational agent (requires voice ID)
python conversational_agent.py
```

## License

This project is open source and available for educational purposes.

## Resources

- [ElevenLabs API Documentation](https://elevenlabs.io/docs)
- [ElevenLabs Voice Cloning](https://elevenlabs.io/voice-cloning)
- [ElevenLabs Conversational AI](https://elevenlabs.io/conversational-ai)

## Support

For ElevenLabs API issues, contact [ElevenLabs Support](https://elevenlabs.io/support)
