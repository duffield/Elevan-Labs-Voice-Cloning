# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

ElevenLabs Voice Clone Conversational AI - an automated pipeline that records voice, clones it via ElevenLabs API, and creates a conversational AI agent using the cloned voice.

## Essential Commands

### Environment Setup
```bash
# Install dependencies (requires Python 3.7+)
pip install -r requirements.txt

# On macOS, if PyAudio installation fails:
brew install portaudio
pip install pyaudio

# Configure API key (required)
cp .env.example .env
# Edit .env and add: ELEVENLABS_API_KEY=your_actual_api_key_here
```

### Running the Application
```bash
# Main application - full automated pipeline
python main.py

# Test individual modules independently
python audio_recorder.py      # Test 30-second voice recording
python voice_cloner.py         # Test voice cloning (requires .env)
python conversational_agent.py # Test agent setup (requires .env and voice_id)
```

## Architecture

### Three-Stage Pipeline
The application follows a sequential workflow orchestrated by `main.py`:
1. **Record** → 2. **Clone** → 3. **Converse**

### Core Components

**`audio_recorder.py` (AudioRecorder)**
- Records 30 seconds of mono audio at 44.1kHz via PyAudio
- Outputs WAV file for voice cloning
- Can be instantiated with custom duration/sample rate

**`voice_cloner.py` (VoiceCloner)**
- Wraps ElevenLabs `voices.add()` API for instant voice cloning
- Returns `(voice_id, cloning_duration)` tuple with performance metrics
- Provides `delete_voice()` for cleanup

**`conversational_agent.py` (ConversationalAgent)**
- Creates ElevenLabs conversational AI agent with cloned voice_id
- Uses `Conversation` class to manage real-time audio sessions
- Agent configuration includes: name, first_message, system_prompt, language

**`main.py`**
- Orchestrates the three-stage pipeline
- Handles error recovery and keyboard interrupts
- Interactive cleanup flow at end (delete voice/agent/audio file)
- All components initialized with API key from environment

### Key Data Flow
```
Audio file → VoiceCloner.clone_voice() → voice_id 
           → ConversationalAgent.create_agent() → agent_id
           → ConversationalAgent.start_conversation()
```

## Important Implementation Details

### API Requirements
- Requires ElevenLabs Starter plan or higher for Instant Voice Cloning
- API key must be in `.env` file (never committed)
- Voice cloning and conversations consume monthly character quota

### Audio Specifications
- Default recording: 30 seconds, 44.1kHz, mono, 16-bit PCM
- Format: WAV (required by ElevenLabs API)
- Microphone permissions required (System Preferences → Security & Privacy)

### Cleanup Behavior
- Application prompts user to delete voice/agent after execution
- Resources are NOT automatically deleted (allows reuse)
- Voice IDs and Agent IDs displayed if kept for later use

### Module Independence
Each module (`audio_recorder.py`, `voice_cloner.py`, `conversational_agent.py`) can run standalone with `if __name__ == "__main__"` test code.

## Development Notes

### Error Handling
- All major operations wrapped in try/except with user-friendly messages
- `KeyboardInterrupt` handled gracefully in main loop
- Cleanup runs in `finally` block to ensure resource management prompts

### Testing Approach
- No formal test framework used
- Test by running modules individually
- Verify microphone/speaker access before running full pipeline

### Platform Compatibility
- Tested on macOS
- Linux support requires `portaudio19-dev python3-pyaudio`
- Windows not tested but should work with PyAudio installed

## Common Issues

### PyAudio Installation
If `pip install pyaudio` fails, install system-level PortAudio first (see Environment Setup).

### API Errors
- Verify API key in `.env` is correct
- Check ElevenLabs account quota at https://elevenlabs.io/app/usage
- Ensure internet connectivity

### Microphone Permissions
Grant Terminal/Python microphone access in System Preferences (macOS).
