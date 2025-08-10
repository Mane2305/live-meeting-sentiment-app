# Live Meeting Sentiment Analysis App

A real-time meeting application built with **Next.js** and **FastAPI** that captures live audio via WebSocket, transcribes it, and applies Natural Language Processing (NLP) to analyze emotions and sentiment in meetings.

---

## Features

- **Real-time audio streaming** through WebSocket  
- **Live transcription** of speech to text  
- **Sentiment and emotion classification** using NLP techniques  
- **Interactive UI** built with Next.js for seamless user experience  

---

## Technology Stack

- **Frontend:** Next.js, React, WebSocket  
- **Backend:** FastAPI, Python NLP libraries (e.g., spaCy, transformers)  
- **Communication:** WebSocket for real-time audio streaming  
- **Version Control:** Git & GitHub  

---

## Getting Started

### Prerequisites

- Node.js >= 14.x  
- Python 3.8+  
- Git  

### Installation



```bash
cd frontend
npm install
npm run dev
cd backend
python -m venv venv
# On Linux/macOS
source venv/bin/activate
# On Windows
venv\Scripts\activate

pip install -r requirements.txt
uvicorn main:app --reload
