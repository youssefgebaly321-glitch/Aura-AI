import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.llm_service import LLMManager
from services.stt_service import verify_deepgram_api_key, DeepgramManager

router = APIRouter()

async def send_json(websocket: WebSocket, type: str, payload: dict):
    """Helper function to send JSON data to the client."""
    await websocket.send_text(json.dumps({"type": type, "payload": payload}))

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🔗 WebSocket connection established")
    
    dg_manager = None
    llm_manager = None
    
    # --- State Management ---
    session_state = {
        "is_muted": False,
        "process_all_speakers": True,
        "is_universally_muted": False # System-wide pause
    }
    transcript_buffer = ""
    buffer_timer = None

    async def process_buffered_transcript():
        nonlocal transcript_buffer
        if transcript_buffer:
            print(f"✅ Processing buffered transcript: {transcript_buffer}")
            if llm_manager:
                answer = await llm_manager.get_ai_answer(transcript_buffer, onboarding_context)
                await send_json(websocket, "ai_answer", {"answer": answer})
                print(f"🤖 AI ANSWER: {answer}")
            else:
                print("⚠️ LLM Manager not initialized, cannot get AI answer.")
            transcript_buffer = "" # Clear buffer after processing

    async def on_transcript(data):
        """Callback function to handle transcripts from Deepgram."""
        nonlocal transcript_buffer, buffer_timer
        try:
            # If universally muted, do not process any transcripts
            if session_state.get("is_universally_muted", False):
                print("⏸️ System paused. Ignoring transcript.")
                return

            await send_json(websocket, "transcript_update", data)

            is_final = data.get('is_final', False)
            transcript = data.get('transcript', '')
            speaker = data.get('speaker')

            # --- Mute-Aware Speaker Logic ---
            # --- Enhanced Mute-Aware Speaker Logic ---
            if session_state["is_muted"]:
                # When muted, treat all speakers as interviewer
                should_process = True
                speaker_label = "Interviewer"
            elif session_state["process_all_speakers"]:
                # When process all speakers enabled, process everyone
                should_process = True
                speaker_label = f"Speaker {speaker}" if speaker is not None else "Unknown Speaker"
            else:
                # Legacy behavior - only process speaker 0 (interviewer)
                should_process = (speaker == 0)
                speaker_label = "Interviewer"

            if transcript and should_process:
                # Add speaker-labeled transcript to buffer
                labeled_transcript = f"{speaker_label}: {transcript}"
                transcript_buffer += labeled_transcript + " "
                
                if buffer_timer and not buffer_timer.done():
                    buffer_timer.cancel()
                
                if is_final:
                    async def delayed_processing():
                        await asyncio.sleep(1.2)
                        await process_buffered_transcript()
                    
                    buffer_timer = asyncio.create_task(delayed_processing())

            elif is_final and not should_process and transcript:
                # Handle candidate response when not processing all speakers
                candidate_response = transcript
                print(f"👤 CANDIDATE (FINAL): {candidate_response}")
                if llm_manager:
                    llm_manager.process_candidate_response(candidate_response)
                
        except WebSocketDisconnect:
            print("🔌 Client disconnected while sending transcript/answer")
        except Exception as e:
            print(f"❌ ERROR: Error in transcript callback: {e}")

    try:
        # 1. Immediately check the Deepgram key upon connection
        print("🔑 Verifying Deepgram API key...")
        is_deepgram_valid = verify_deepgram_api_key()
        await send_json(websocket, "api_key_status", {"service": "deepgram", "valid": is_deepgram_valid})
        # AI provider verification is now done on the frontend before starting

        # 2. Listen for messages from the client
        while True:
            message = await websocket.receive()
            if 'text' in message:
                data = json.loads(message['text'])
                if data['type'] == 'start_interview':
                    print("🎬 Starting interview session...")
                    payload = data.get('payload', {})
                    provider_config = payload.get('aiProvider')
                    onboarding_context = payload.get('onboardingData', {})
                    session_state["is_muted"] = payload.get('is_muted', False)
                    session_state["process_all_speakers"] = payload.get('process_all_speakers', True)
                    session_state["is_universally_muted"] = payload.get('is_universally_muted', False)

                    if not provider_config:
                        print("❌ Cannot start interview: AI provider not selected.")
                        await send_json(websocket, "error", {"message": "AI provider not selected."})
                        return

                    # Load provider details from JSON config
                    with open("ai_providers.json", "r") as f:
                        providers = json.load(f)
                    
                    selected_provider = next((p for p in providers if p["name"] == provider_config.get("name")), None)

                    if not selected_provider:
                        print(f"❌ Provider '{provider_config.get('name')}' not found in config.")
                        return
                        
                    # Create a new LLMManager for this session
                    llm_manager = LLMManager(
                        provider_name=selected_provider.get("name"),
                        base_url=selected_provider.get("baseURL"),
                        api_key=selected_provider.get("apiKey"),
                        model_name=provider_config.get("model")
                    )
                    
                    # Log the context we received for debugging
                    print(f"📋 Interview context loaded:")
                    print(f"   - Name: {onboarding_context.get('name', 'Not provided')}")
                    print(f"   - Company: {onboarding_context.get('company', 'Not provided')}")
                    print(f"   - Role: {onboarding_context.get('role', 'Not provided')}")
                    print(f"   - Focus areas: {onboarding_context.get('focus', [])}")
                    
                    dg_manager = DeepgramManager(on_transcript)
                    await dg_manager.start()
                elif data['type'] == 'config_update':
                    payload = data.get('payload', {})
                    if 'processAllSpeakers' in payload:
                        session_state["process_all_speakers"] = payload['processAllSpeakers']
                        print(f"🎯 Process All Speakers config updated: {session_state['process_all_speakers']}")
                    if 'isUniversallyMuted' in payload:
                        session_state["is_universally_muted"] = payload['isUniversallyMuted']
                        print(f"⏸️ Universal Mute config updated: {session_state['is_universally_muted']}")
                elif data['type'] == 'audio_chunk':
                    if dg_manager:
                        # If universally muted, do not process audio chunks
                        if session_state.get("is_universally_muted", False):
                            # Log occasionally to confirm it's working
                            # print("⏸️ System paused. Ignoring audio chunk.")
                            return

                        payload = data.get('payload', {})
                        audio_data = bytes(payload.get('audio', []))
                        session_state["is_muted"] = payload.get('is_muted', False) # Update mic mute state
                        
                        if len(audio_data) > 0:
                            await dg_manager.send_audio(audio_data)
                        else:
                            print("⚠️ WARNING: Received empty audio data")
                elif data['type'] == 'end_interview':
                    print("🛑 Ending interview session...")
                    if dg_manager:
                        await dg_manager.finish()
                    break  # End the session
            elif 'bytes' in message: # Legacy support, should be deprecated
                if dg_manager:
                    audio_data = message['bytes']
                    if len(audio_data) > 0:
                        await dg_manager.send_audio(audio_data)
                    else:
                        print("⚠️ WARNING: Received empty audio data")
                else:
                    print("⚠️ WARNING: Received audio but dg_manager is None")

    except WebSocketDisconnect:
        print("🔌 WebSocket connection closed by client")
    except Exception as e:
        print(f"❌ ERROR: WebSocket error: {e}")
    finally:
        if dg_manager:
            await dg_manager.finish()
        print("🧹 WebSocket resources cleaned up")