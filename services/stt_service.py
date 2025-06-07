import asyncio
import requests
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
)
from core.config import settings

def verify_deepgram_api_key():
    """
    Verifies the Deepgram API key by making a direct HTTP request.
    This is the most reliable method, independent of SDK changes.
    Returns True if the key is valid, False otherwise.
    """
    if not settings.DEEPGRAM_API_KEY:
        return False

    url = "https://api.deepgram.com/v1/projects"
    headers = {
        "Authorization": f"Token {settings.DEEPGRAM_API_KEY}"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print("INFO: Deepgram API key is valid.")
            return True
        else:
            print(f"ERROR: Deepgram API key verification failed. Status: {response.status_code}, Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"ERROR: A network error occurred while verifying Deepgram key: {e}")
        return False


class DeepgramManager:
    """
    Manages the connection to Deepgram for live transcription.
    """
    def __init__(self, transcript_callback):
        self.transcript_callback = transcript_callback
        self.dg_connection = None
        self.is_connected = False
        self.stop_event = asyncio.Event()
        
        # Setup Deepgram client
        config = DeepgramClientOptions(
            verbose=settings.LOG_LEVEL,
            options={"keepalive": "true"}
        )
        self.deepgram = DeepgramClient(settings.DEEPGRAM_API_KEY, config)

    async def start(self):
        """Starts the Deepgram transcription connection."""
        self.dg_connection = self.deepgram.listen.asynclive.v("1")
        
        self.dg_connection.on(LiveTranscriptionEvents.Open, self.on_open)
        self.dg_connection.on(LiveTranscriptionEvents.Transcript, self.on_message)
        self.dg_connection.on(LiveTranscriptionEvents.Error, self.on_error)
        self.dg_connection.on(LiveTranscriptionEvents.Close, self.on_close)

        options = LiveOptions(
            model="nova-2",
            language="en-US",
            smart_format=True,
            encoding="linear16",
            channels=1,
            sample_rate=48000,
            # Enable Diarization
            diarize=True, 
        )
        
        try:
            await self.dg_connection.start(options)
            print("INFO: Deepgram connection started.")
        except Exception as e:
            print(f"ERROR: Could not start Deepgram connection: {e}")

    async def on_open(self, *args, **kwargs):
        print("INFO: Deepgram connection opened.")
        self.is_connected = True

    async def on_message(self, *args, **kwargs):
        if self.stop_event.is_set():
            return
        result = kwargs['result']
        transcript = result.channel.alternatives[0].transcript
        if len(transcript) > 0:
            await self.transcript_callback({
                "speaker": result.channel.json.get('speaker', 0),
                "transcript": transcript
            })

    async def on_error(self, *args, **kwargs):
        if self.stop_event.is_set():
            return
        error = kwargs['error']
        print(f"ERROR: Deepgram error: {error}")

    async def on_close(self, *args, **kwargs):
        print("INFO: Deepgram connection closed.")
        self.is_connected = False

    async def send_audio(self, audio_chunk):
        """Sends an audio chunk to Deepgram."""
        if self.is_connected and self.dg_connection and not self.stop_event.is_set():
            await self.dg_connection.send(audio_chunk)

    async def finish(self):
        """Signals the connection to close and finishes it."""
        print("INFO: Signaling Deepgram connection to finish.")
        self.stop_event.set()
        if self.dg_connection:
            await self.dg_connection.finish()
            print("INFO: Finished Deepgram connection.")