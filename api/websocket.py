import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.llm_service import verify_groq_api_key, get_ai_suggestion
from services.stt_service import verify_deepgram_api_key, DeepgramManager

router = APIRouter()

async def send_json(websocket: WebSocket, type: str, payload: dict):
    """Helper function to send JSON data to the client."""
    await websocket.send_text(json.dumps({"type": type, "payload": payload}))

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("INFO: WebSocket connection established.")
    
    dg_manager = None
    onboarding_context = {}

    async def on_transcript(data):
        """Callback function to handle transcripts from Deepgram."""
        try:
            # First, send the raw transcript to the client for display
            await send_json(websocket, "transcript_update", data)

            # Now, check if it's the interviewer speaking and get a suggestion
            # Note: Diarization might label speakers differently. We assume '1' is the interviewer for now.
            if data.get('speaker') == 1 and data.get('transcript'):
                print(f"INFO: Interviewer said: {data['transcript']}")
                suggestion = get_ai_suggestion(data['transcript'], onboarding_context)
                await send_json(websocket, "suggestion_update", {"suggestion": suggestion})
        except WebSocketDisconnect:
            print("INFO: Client disconnected while sending transcript/suggestion.")
        except Exception as e:
            print(f"ERROR: Error in on_transcript callback: {e}")

    try:
        # 1. Immediately check the keys upon connection
        print("INFO: Verifying API keys...")
        is_deepgram_valid = verify_deepgram_api_key()
        is_groq_valid = verify_groq_api_key()
        await send_json(websocket, "api_key_status", {"service": "deepgram", "valid": is_deepgram_valid})
        await send_json(websocket, "api_key_status", {"service": "groq", "valid": is_groq_valid})

        # 2. Listen for messages from the client
        while True:
            message = await websocket.receive()
            if 'text' in message:
                data = json.loads(message['text'])
                if data['type'] == 'start_interview':
                    print("INFO: Received 'start_interview' message.")
                    onboarding_context = data.get('payload', {})
                    dg_manager = DeepgramManager(on_transcript)
                    await dg_manager.start()
                elif data['type'] == 'end_interview':
                    print("INFO: Received 'end_interview' message.")
                    if dg_manager:
                        await dg_manager.finish()
                    break  # End the session
            elif 'bytes' in message:
                if dg_manager:
                    await dg_manager.send_audio(message['bytes'])

    except WebSocketDisconnect:
        print("INFO: WebSocket connection closed by client.")
    except Exception as e:
        print(f"ERROR: An error occurred in the WebSocket: {e}")
    finally:
        if dg_manager:
            await dg_manager.finish()
        print("INFO: Cleaned up WebSocket resources.")