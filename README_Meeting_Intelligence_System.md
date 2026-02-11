
# Real-Time Meeting Intelligence System

This project is a full-stack real-time meeting application that performs live speech transcription and sentiment analysis during video calls.  
It combines video conferencing, WebSocket-based audio streaming, backend processing, and NLP analysis into a single integrated system.

The main objective of this project was to explore how AI pipelines can be embedded into real-time communication platforms.

---

## What This Project Does

• Captures live audio from meetings  
• Streams audio to backend via WebSocket  
• Trims silence and preprocesses audio  
• Sends audio for speech-to-text transcription  
• Applies sentiment and emotion analysis on transcript  
• Saves structured results to the server  
• Displays results in the UI  

---

## Why I Built This

Traditional meeting apps focus only on communication.  
I wanted to experiment with adding intelligence to meetings — understanding tone, emotion, and overall sentiment automatically.

This project helped me understand:

- Real-time data streaming
- Backend pipeline design
- Audio preprocessing
- NLP model integration
- Full-stack architecture coordination

---

## System Architecture Overview

Frontend (Next.js + TypeScript)
- Authentication (Clerk)
- Meeting dashboard
- WebRTC-based video
- WebSocket audio streaming
- UI interaction & state management

Backend (FastAPI + Python)
- WebSocket audio receiver
- Silence trimming
- Audio upload handling
- Speech-to-text transcription (AssemblyAI API)
- Sentiment and emotion classification
- Transcript storage

Communication Layer
- WebSocket for streaming
- REST endpoints for processing

---

## End-to-End Flow

1. User joins or creates a meeting  
2. Audio stream is sent to backend  
3. Silence trimming is applied  
4. Audio is uploaded for transcription  
5. Transcript is received  
6. Sentiment + emotion analysis runs  
7. Results are saved in:

backend/transcriptions/transcription_with_analysis.txt

---

## Example Output

Transcription:
Hello everyone. We are starting today's project discussion.

Sentiment: Neutral  
Emotions: {'joy': 1, 'anger': 0}

---

## Tech Stack

Frontend
- Next.js
- React
- TypeScript
- WebRTC
- Tailwind CSS

Backend
- FastAPI
- Python 3.8+
- WebSocket
- AssemblyAI API
- NLP libraries (spaCy / Transformers)

---

## Project Structure

project-root/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── actions/
│   └── package.json
│
├── backend/
│   ├── main.py
│   ├── recorded_audios/
│   ├── transcriptions/
│   └── requirements.txt
│
└── README.md

---

## Installation Guide

Clone the repository:

git clone https://github.com/your-username/project-name.git
cd project-name

---

Frontend Setup

cd frontend
npm install
npm run dev

Runs at:
http://localhost:3000

---

Backend Setup

cd backend
python -m venv venv

Activate virtual environment:

Windows:
venv\Scripts\activate

Mac/Linux:
source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Run server:

uvicorn main:app --reload

Runs at:
http://localhost:8000

---

## Engineering Notes

- WebSocket chosen for low-latency streaming
- Silence trimming reduces unnecessary transcription cost
- Modular NLP pipeline allows future model upgrades
- Designed to support future Docker or cloud deployment

---

## Future Improvements

- Real-time sentiment visualization dashboard
- Replace API transcription with open-source ASR model
- Docker containerization
- Cloud deployment
- Model evaluation metrics logging
- Meeting-level sentiment summary analytics

---

Author: Saurabh Mane
