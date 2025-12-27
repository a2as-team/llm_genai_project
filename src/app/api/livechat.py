import json
import asyncio
import base64
import logging
import uuid
from typing import Optional
from dotenv import load_dotenv

from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from google.genai.types import (
    Part,
    Content,
    Blob,
)
from google.genai import types

from google.adk.runners import Runner
from google.adk.sessions.database_session_service import DatabaseSessionService
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode

from src.agents.root_agent.rootAgent import root_agent
from src.config import app_settings, gemini_settings, database_settings
from src.utils.context import set_request_context, clear_request_context

load_dotenv()

router = APIRouter(tags=["LiveChat"])
logger = logging.getLogger(__name__)

db_session_service = DatabaseSessionService(
    db_url=database_settings.dsn
)

async def start_agent_session(user_id: str, session_id: Optional[str] = None):
    """Starts an agent session"""

    # Initialize the request context for this session (thread-safe, async-safe)
    # This makes the session_id and user_id available to all tools via contextvars
 # 1. Initialize context variables (ID, User)
    set_request_context(session_id=session_id, user_id=user_id)
    
    # 2. CRUCIAL : Initialiser l'objet mutable (Order) ICI dans le scope parent
    # Ainsi, le Runner et ses outils partageront tous la MEME référence à cet objet.
    logger.info(f"Request context initialized for user={user_id}, session={session_id}")

    # Look for existing session (in memory OR in database)
    session = None        
    if session_id:
        
        session = await db_session_service.get_session(
            app_name=app_settings.APP_NAME, user_id=user_id, session_id=session_id
        )
        
        if session:
            logger.info(f"Session found in database: {session_id}")
        else:
            # Session doesn't exist anywhere
            logger.warning(f"Session {session_id} not found (memory or database)")
            # Create new session in DB for this session_id
            session = await db_session_service.create_session(
                app_name=app_settings.APP_NAME, 
                user_id=user_id,
                session_id=session_id
            )

            logger.info(f"New session created in database: {session_id}")

    else:
        # No session_id provided, create new one in DB
        session = await db_session_service.create_session(
            app_name=app_settings.APP_NAME, user_id=user_id
        )
        session_id = session.id    
        logger.info(f"New session created in database: {session_id}")

    # Create a Runner
    runner = Runner(
        app_name=app_settings.APP_NAME,
        agent=root_agent,
        session_service=db_session_service
    )

    # Create a LiveRequestQueue for this session
    live_request_queue = LiveRequestQueue()

    # Setup RunConfig 
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        realtime_input_config=types.RealtimeInputConfig(
            automatic_activity_detection=types.AutomaticActivityDetection(
                start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_HIGH,
                end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
                prefix_padding_ms=200,
                silence_duration_ms=400,
            ),
            activity_handling=types.ActivityHandling.START_OF_ACTIVITY_INTERRUPTS,
            turn_coverage=types.TurnCoverage.TURN_INCLUDES_ONLY_ACTIVITY,
        ),
        response_modalities = [types.Modality.AUDIO],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=gemini_settings.AGENT_VOICE
                )
            ),
            language_code=gemini_settings.AGENT_LANGUAGE
        ),
        proactivity=types.ProactivityConfig(
            proactive_audio=True,
        ),        
    )

    # Start agent session
    live_events = runner.run_live(
        user_id=user_id,
        session_id=session_id,
        live_request_queue=live_request_queue,
        run_config=run_config,
    )
    return live_events, live_request_queue, session_id


async def agent_to_client_messaging(websocket: WebSocket, live_events):
    """Agent to client communication: Sends structured event data."""
    print("=" * 80)
    print("🚀 START: agent_to_client_messaging INITIALIZED")
    print("=" * 80)
    try:
        interaction_count = 0
        async for event in live_events:
            try:
                # Only log meaningful events, skip audio chunks
                if event.content and event.content.parts:
                    has_text = any(part.text for part in event.content.parts)
                    has_function = any(part.function_call or part.function_response for part in event.content.parts)
                    
                    if has_text or has_function or event.turn_complete:
                        interaction_count += 1
                        print("\n" + "─" * 80)
                        print(f"📥 INTERACTION #{interaction_count} START")
                        print(f"   Event Type: {type(event).__name__}")
                        print(f"   Author: {event.author}")
                        print(f"   Partial: {event.partial} | Turn Complete: {event.turn_complete}")
                        print("─" * 80)
                
                logger.info(f"Received event type: {type(event)}")
                logger.debug(f"Event details: {event}")            
                
                message_to_send = {
                    "author": event.author or "agent",
                    "is_partial": event.partial or False,
                    "turn_complete": event.turn_complete or False,
                    "interrupted": event.interrupted or False,
                    "parts": [],
                    "input_transcription": None,
                    "output_transcription": None
                }

                if not event.content:
                    logger.debug("Event has no content")
                    if (message_to_send["turn_complete"] or message_to_send["interrupted"]):
                        logger.info(f"Sending control message: turn_complete={message_to_send['turn_complete']}, interrupted={message_to_send['interrupted']}")
                        await websocket.send_text(json.dumps(message_to_send))
                    continue 

                logger.info(f"Processing event content with {len(event.content.parts)} parts")
                transcription_text = "".join(part.text for part in event.content.parts if part.text)
                
                if hasattr(event.content, "role") and event.content.role == "user":
                    if transcription_text:
                        print(f"   👤 User: {transcription_text}")
                        message_to_send["input_transcription"] = {
                            "text": transcription_text,
                            "is_final": not event.partial
                        }
                
                else:
                    if transcription_text:
                        print(f"   🤖 Agent: {transcription_text}")
                        message_to_send["output_transcription"] = {
                            "text": transcription_text,
                            "is_final": not event.partial
                        }
                        message_to_send["parts"].append({"type": "text", "data": transcription_text})

                    for part in event.content.parts:
                        if part.inline_data and part.inline_data.mime_type.startswith("audio/pcm"):
                            audio_data = part.inline_data.data
                            encoded_audio = base64.b64encode(audio_data).decode("ascii")
                            message_to_send["parts"].append({"type": "audio/pcm", "data": encoded_audio})
                        
                        elif part.function_call:
                            print(f"   🔧 Function Call: {part.function_call.name}")
                            print(f"      Args: {part.function_call.args}")
                            message_to_send["parts"].append({
                                "type": "function_call", 
                                "data": {
                                    "name": part.function_call.name, 
                                    "args": part.function_call.args or {}
                                }
                            })
                        

                if (message_to_send["parts"] or 
                    message_to_send["turn_complete"] or
                    message_to_send["interrupted"] or
                    message_to_send["input_transcription"] or
                    message_to_send["output_transcription"]):
                    
                    await websocket.send_text(json.dumps(message_to_send))
                    
                    if event.turn_complete:
                        print("─" * 80)
                        print(f"✅ INTERACTION #{interaction_count} END (Turn Complete)")
                        print("─" * 80 + "\n")

            except Exception as e:
                print(f"❌ ERROR processing event: {e}")
                logger.error(f"Error processing event: {e}", exc_info=True)

    except Exception as e:
        print("=" * 80)
        print(f"❌ FATAL ERROR in agent_to_client_messaging: {e}")
        print("=" * 80)
        logger.error(f"Error in agent_to_client_messaging loop: {e}", exc_info=True)

async def client_to_agent_messaging(websocket: WebSocket, live_request_queue: LiveRequestQueue):
    """Client to agent communication"""
    print("=" * 80)
    print("🚀 START: client_to_agent_messaging INITIALIZED")
    print("=" * 80)
    message_count = 0
    try:
        while True:
            try:
                message_json = await websocket.receive_text()
                message = json.loads(message_json)
                mime_type = message["mime_type"]
                message_count += 1

                if mime_type == "text/plain":
                    data = message["data"]
                    print(f"\n📤 CLIENT MESSAGE #{message_count} (text/plain)")
                    print(f"   Content: {data}")
                    content = Content(role="user", parts=[Part.from_text(text=data)])
                    live_request_queue.send_content(content=content)
                    print(f"✅ Sent to agent queue")

                elif mime_type == "audio/pcm":
                    data = message["data"]
                    decoded_data = base64.b64decode(data)
                    live_request_queue.send_realtime(Blob(data=decoded_data, mime_type=mime_type))
                    
                else:
                    print(f"\n⚠️  UNSUPPORTED MIME TYPE: {mime_type}")
                    logger.warning(f"Mime type not supported: {mime_type}")

            except WebSocketDisconnect:
                print("\n" + "=" * 80)
                print("🔴 Client disconnected (WebSocketDisconnect)")
                print("=" * 80)
                logger.info("Client disconnected (WebSocketDisconnect).")
                break

            except Exception as e:
                print(f"\n❌ ERROR in client_to_agent_messaging: {e}")
                logger.error(f"An error occurred in client_to_agent_messaging: {e}")
    except Exception as e:
        print("=" * 80)
        print(f"❌ FATAL ERROR in client_to_agent_messaging loop: {e}")
        print("=" * 80)
        logger.error(f"Fatal error in client_to_agent_messaging: {e}")


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: Optional[str] = None, 
    session_id: Optional[str] = None
):
    """Client websocket endpoint
    
    Args:
        websocket: WebSocket connection
        user_id: Optional user ID (auto-generated UUID if not provided)
        session_id: Optional session ID (auto-generated if not provided)
    """

    # Wait for client connection
    await websocket.accept()

    # Generate user_id if not provided
    user_id_str = user_id if user_id else str(uuid.uuid4())
    
    print("\n" + "=" * 80)
    print(f"🔗 NEW WEBSOCKET CONNECTION")
    print(f"   User ID: {user_id_str}" + (" (auto-generated)" if not user_id else ""))
    print(f"   Session ID: {session_id}" + (" (will be generated)" if not session_id else ""))
    print("=" * 80)
    
    live_events, live_request_queue, session_id = await start_agent_session(user_id_str, session_id)
    
    # Send session ID and user ID to client
    await websocket.send_text(json.dumps({
        "session_id": session_id,
        "user_id": user_id_str
    }))
    print(f"✅ Session initialized: {session_id}\n")

    #debug
    if live_events and live_request_queue:
        print("✅ Live events and live request queue created\n")

    # Start tasks
    agent_to_client_task = asyncio.create_task(
        agent_to_client_messaging(websocket, live_events)
    )
    client_to_agent_task = asyncio.create_task(
        client_to_agent_messaging(websocket, live_request_queue)
    )

    # Wait until the websocket is disconnected or an error occurs
    tasks = [agent_to_client_task, client_to_agent_task]
    await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

    # Close LiveRequestQueue
    live_request_queue.close()
    
    # Clear the request context to avoid leaks
    clear_request_context()
    logger.info(f"Request context cleared for user {user_id}")
    
    print("\n" + "=" * 80)
    print(f"🔌 CONNECTION CLOSED")
    print(f"   User ID: {user_id}")
    print(f"   Session ID: {session_id}")
    print("=" * 80 + "\n")
