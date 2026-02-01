# Audio Transcriber

A Flask web app that transcribes audio files using Groq's Whisper API

## Features
- Upload audio files(mp3,wav,m4a,ogg)
- Automatic Transcription using Whisper Large V3
- Clean, responsive web interface
- Real time Transcription feedback

## Tech stack
- **Backend:** Flask (Python)
- **API:** Groq Whisper Large V3    
- **Frontend:** HTML, CSS, and JavaScript
- **Deployment:** Railway

## Live Demo
[Will be deployed on Railway later]

## Setup Locally

1. Clone the repository:
```bash
git clone https://github.com/Shaurya-900/audio-transcriber.git
cd audio-transcriber
```

2. Insrall dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```
GROQ_API_KEY=api_key_here
```

4. Run the app:
```bash
python app.py
```
5. Visit `http://localhost:5000/transcribe`

## Deployment

Deployed on Railway with automatic deployment from Github.

Built as a side project to learn how Flask and Javascript embedded into HTML works

## License

MIT