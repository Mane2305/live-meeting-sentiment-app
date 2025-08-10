import asyncio
import websockets
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import aiohttp
import os
from dotenv import load_dotenv
import wave
import contextlib
import logging
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from collections import defaultdict
from pydub import AudioSegment  # Import pydub for silence trimming
from pydub.silence import split_on_silence


# Load environment variables
load_dotenv()

# Initialize Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
ASSEMBLYAI_UPLOAD_URL = "https://api.assemblyai.com/v2/upload"
ASSEMBLYAI_TRANSCRIPT_URL = "https://api.assemblyai.com/v2/transcript"
ASSEMBLYAI_TRANSCRIPT_STATUS_URL = "https://api.assemblyai.com/v2/transcript/{transcript_id}"

# FastAPI app instance
app = FastAPI()

# Constants and directories
AUDIO_FILE_PATH = "audio.wav"
TRANSCRIPTION_FOLDER = "transcriptions"
os.makedirs(TRANSCRIPTION_FOLDER, exist_ok=True)

# Audio queue
audio_queue = asyncio.Queue()

# Download VADER lexicon for sentiment analysis
nltk.download('vader_lexicon')

# Initialize SentimentIntensityAnalyzer for VADER sentiment analysis
sia = SentimentIntensityAnalyzer()

def save_audio(audio_data):
    """Saves received audio data to a file and verifies its integrity."""
    if not audio_data:
        logger.warning("⚠️ Warning: No audio data received, skipping save.")
        return False
    
    logger.info("📝 Saving audio data...")
    try:
        with wave.open(AUDIO_FILE_PATH, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(audio_data)
        
        # Verify the integrity of the audio file
        with contextlib.closing(wave.open(AUDIO_FILE_PATH, 'r')) as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate)
            logger.info(f"🔍 Saved audio details: {frames} frames, {rate} Hz, duration: {duration:.2f} sec")

        logger.info("✅ Audio saved successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error saving audio file: {e}")
        return False

def trim_leading_silence(audio_path, silence_thresh=-40, min_silence_len=500):
    """Trims leading silence from the audio file before sending to AssemblyAI."""
    try:
        sound = AudioSegment.from_wav(audio_path)

        # Split the audio based on silence
        chunks = split_on_silence(sound, min_silence_len=min_silence_len, silence_thresh=silence_thresh)

        # If there's any chunk found, we will consider the first non-silent chunk
        if chunks:
            trimmed_sound = chunks[0]
        
            # Save the trimmed audio
            trimmed_audio_path = "trimmed_audio.wav"
            trimmed_sound.export(trimmed_audio_path, format="wav")
            logger.info("🎧 Leading silence trimmed successfully.")
            return trimmed_audio_path
        else:
            logger.warning("⚠️ No audio detected after trimming silence.")
            return audio_path  # Return the original audio if no chunk is detected after trimming
    except Exception as e:
        logger.error(f"❌ Error trimming silence: {e}")
        return audio_path  # Return original if trimming fails

async def upload_audio():
    """Uploads the saved audio file to AssemblyAI and retrieves the transcription."""
    if not ASSEMBLYAI_API_KEY:
        logger.error("❌ Error: AssemblyAI API key is missing!")
        return
    
    if not os.path.exists(AUDIO_FILE_PATH):
        logger.error("❌ Error: Audio file not found!")
        return
    
    logger.info("🚀 Uploading audio...")
    headers = {"authorization": ASSEMBLYAI_API_KEY}
    try:
        with open(AUDIO_FILE_PATH, "rb") as f:
            async with aiohttp.ClientSession() as session:
                async with session.post(ASSEMBLYAI_UPLOAD_URL, headers=headers, data=f) as response:
                    if response.status != 200:
                        logger.error(f"❌ Upload failed with status {response.status}")
                        response_text = await response.text()
                        logger.error(f"Upload failed: {response_text}")
                        return
                    
                    result = await response.json()
                    audio_url = result.get("upload_url")
                    if not audio_url:
                        logger.error("❌ Error: Upload URL not received!")
                        return
                    logger.info(f"🎤 Audio uploaded, URL: {audio_url}")

                    # Continue with transcription
                    data = {"audio_url": audio_url}
                    async with session.post(ASSEMBLYAI_TRANSCRIPT_URL, headers=headers, json=data) as transcription_response:
                        if transcription_response.status != 200:
                            logger.error(f"❌ Transcription request failed with status {transcription_response.status}")
                            return
                        transcript_data = await transcription_response.json()
                        transcript_id = transcript_data.get("id")
                        if not transcript_id:
                            logger.error("❌ Error: No transcript ID received!")
                            return
                        logger.info(f"🆔 Transcript request ID: {transcript_id}")
                        
                        # Wait for transcription to complete
                        await check_transcription_status(transcript_id, headers)

    except Exception as e:
        logger.error(f"❌ Error during audio upload: {e}")

async def check_transcription_status(transcript_id, headers):
    """Checks the status of the transcription and fetches the result when ready."""
    try:
        async with aiohttp.ClientSession() as session:
            # Poll for transcription status
            while True:
                async with session.get(ASSEMBLYAI_TRANSCRIPT_STATUS_URL.format(transcript_id=transcript_id), headers=headers) as status_response:
                    if status_response.status != 200:
                        logger.error(f"❌ Transcription status check failed with status {status_response.status}")
                        return
                    
                    status_data = await status_response.json()
                    status = status_data.get("status")
                    if status == "completed":
                        logger.info("🎉 Transcription completed successfully!")
                        transcription_text = status_data.get("text", "")
                        if transcription_text:
                            logger.info(f"📝 Transcription text received: {transcription_text[:200]}...")  # Log a snippet of the text
                            await save_transcription_to_txt(transcription_text)
                        else:
                            logger.error("❌ No transcription text found!")
                            logger.error(f"⚠️ Full status response: {status_data}")  # Log the full response for further debugging
                        return
                    elif status == "failed":
                        logger.error("❌ Transcription failed!")
                        logger.error(f"⚠️ Full status response: {status_data}")  # Log the full response in case of failure
                        return
                    logger.info("⏳ Waiting for transcription to complete...")
                    await asyncio.sleep(5)  # Wait for 5 seconds before retrying
    except Exception as e:
        logger.error(f"❌ Error while checking transcription status: {e}")

async def save_transcription_to_txt(transcription_text):
    """Saves the transcription text along with sentiment and emotion analysis to a .txt file."""
    try:
        # Perform sentiment and emotion analysis
        sentiment, emotions = analyze_sentiment_and_emotions(transcription_text)

        # Save transcription and analysis results to text file
        transcription_file_path = os.path.join(TRANSCRIPTION_FOLDER, "transcription_with_analysis.txt")
        with open(transcription_file_path, "w") as f:
            f.write(f"Transcription: {transcription_text}\n\n")
            f.write(f"Sentiment: {sentiment}\n")
            f.write(f"Emotions: {emotions}\n")

        logger.info(f"✅ Transcription and analysis saved to {transcription_file_path}")
    except Exception as e:
        logger.error(f"❌ Error saving transcription to file: {e}")

def analyze_sentiment_and_emotions(text):
    """Analyzes sentiment and emotions using NRC Lexicon and VADER."""
    # Sentiment Analysis with VADER
    sentiment_score = sia.polarity_scores(text)
    sentiment = "Neutral"
    if sentiment_score['compound'] >= 0.05:
        sentiment = "Positive"
    elif sentiment_score['compound'] <= -0.05:
        sentiment = "Negative"

    # Emotion Analysis using simple keyword matching (NRC Lexicon logic can be expanded)
    emotions = defaultdict(int)
    emotion_keywords = {
        'joy': ['happy', 'joyful', 'excited', 'elated'],
        'anger': ['angry', 'frustrated', 'irritated', 'rage'],
        'sadness': ['sad', 'depressed', 'unhappy', 'down'],
        'fear': ['afraid', 'scared', 'fear', 'nervous']
    }

    for emotion, keywords in emotion_keywords.items():
        for keyword in keywords:
            if keyword in text.lower():
                emotions[emotion] += 1

    return sentiment, dict(emotions)

async def process_audio_data(audio_data):
    """Process audio data received from WebSocket and trigger upload."""
    if audio_data:
        logger.info("📝 Processing and uploading saved audio...")
        if save_audio(audio_data):
            trimmed_audio_path = trim_leading_silence(AUDIO_FILE_PATH)  # Trim silence before uploading
            await upload_audio()

@app.websocket("/ws/captions")
async def websocket_endpoint(websocket: WebSocket):
    """Handles WebSocket connections for real-time audio processing."""
    await websocket.accept()
    logger.info("✅ WebSocket connected")
    
    audio_data = bytearray()
    try:
        while True:
            chunk = await websocket.receive_bytes()
            audio_data.extend(chunk)
            logger.info(f"🎧 Received audio chunk of size: {len(chunk)} bytes")
    
    except WebSocketDisconnect:
        logger.warning("❌ WebSocket disconnected")
    
    finally:
        # Process the received audio
        await process_audio_data(audio_data)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
