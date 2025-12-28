import json
import asyncio
import base64
import logging
import uuid
import re
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

# Patterns to detect when agent claims to have done something
# These are French phrases that indicate a confirmation of an action
CONFIRMATION_PATTERNS = [
    # Order confirmations
    r"commande.*enregistr[ée]",
    r"commande.*valid[ée]",
    r"commande.*confirm[ée]",
    r"j'ai.*enregistr[ée].*commande",
    r"votre commande.*prise",
    r"c'est not[ée]",
    # Booking confirmations
    r"r[ée]servation.*confirm[ée]",
    r"r[ée]servation.*enregistr[ée]",
    r"table.*r[ée]serv[ée]",
    r"j'ai.*r[ée]serv[ée]",
    r"r[ée]servation.*valid[ée]",
    # Cancellation confirmations
    r"r[ée]servation.*annul[ée]",
    r"j'ai.*annul[ée]",
    r"annulation.*confirm[ée]",
]

# Tools that MUST be called before certain confirmations
REQUIRED_TOOLS_FOR_ACTION = {
    "order": ["validate_order"],
    "booking": ["validate_booking"],
    "cancel": ["cancel_booking"],
}

def detect_confirmation_without_tool(text: str, tools_called_in_turn: set) -> Optional[str]:
    """
    Detect if the agent is confirming an action without having called the required tool.
    Returns a warning message if detected, None otherwise.
    """
    text_lower = text.lower()
    
    for pattern in CONFIRMATION_PATTERNS:
        if re.search(pattern, text_lower):
            # Determine which type of action this is
            if any(word in text_lower for word in ["commande", "commandé"]):
                action_type = "order"
            elif any(word in text_lower for word in ["annul"]):
                action_type = "cancel"
            elif any(word in text_lower for word in ["réserv", "reserv", "table"]):
                action_type = "booking"
            else:
                continue
            
            # Check if the required tool was called
            required_tools = REQUIRED_TOOLS_FOR_ACTION.get(action_type, [])
            if not any(tool in tools_called_in_turn for tool in required_tools):
                return f"⚠️ HALLUCINATION DETECTED: Agent confirmed '{action_type}' action but never called {required_tools}. Pattern matched: '{pattern}'"
    
    return None


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
    logger.info("Agent-to-client messaging started")
    
    # Track tool calls within the current turn to detect hallucinations
    tools_called_in_turn: set = set()
    accumulated_text_in_turn: str = ""
    
    try:
        async for event in live_events:
            try:
                # Log meaningful events at DEBUG level (skip audio chunks for noise reduction)
                if event.content and event.content.parts:
                    has_text = any(part.text for part in event.content.parts)
                    has_function = any(part.function_call or part.function_response for part in event.content.parts)
                    
                    if has_text or has_function:
                        logger.debug(f"Event: author={event.author}, partial={event.partial}, turn_complete={event.turn_complete}")            
                
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
                    if (message_to_send["turn_complete"] or message_to_send["interrupted"]):
                        logger.debug(f"Control message: turn_complete={message_to_send['turn_complete']}, interrupted={message_to_send['interrupted']}")
                        
                        # At turn end, check for hallucinations in accumulated text
                        if accumulated_text_in_turn:
                            warning = detect_confirmation_without_tool(accumulated_text_in_turn, tools_called_in_turn)
                            if warning:
                                logger.warning(warning)
                                logger.warning(f"Tools called this turn: {tools_called_in_turn}")
                                logger.warning(f"Agent text this turn: {accumulated_text_in_turn[:300]}...")
                        
                        # Reset tracking for next turn
                        tools_called_in_turn.clear()
                        accumulated_text_in_turn = ""
                        
                        await websocket.send_text(json.dumps(message_to_send))
                    continue 

                transcription_text = "".join(part.text for part in event.content.parts if part.text)
                
                if hasattr(event.content, "role") and event.content.role == "user":
                    if transcription_text:
                        logger.info(f"User transcription: {transcription_text[:100]}..." if len(transcription_text) > 100 else f"User transcription: {transcription_text}")
                        message_to_send["input_transcription"] = {
                            "text": transcription_text,
                            "is_final": not event.partial
                        }
                        # User speaking = new turn, reset tracking
                        tools_called_in_turn.clear()
                        accumulated_text_in_turn = ""
                
                else:
                    if transcription_text:
                        logger.info(f"Agent response: {transcription_text[:100]}..." if len(transcription_text) > 100 else f"Agent response: {transcription_text}")
                        message_to_send["output_transcription"] = {
                            "text": transcription_text,
                            "is_final": not event.partial
                        }
                        message_to_send["parts"].append({"type": "text", "data": transcription_text})
                        
                        # Accumulate text for hallucination detection
                        accumulated_text_in_turn += " " + transcription_text

                    for part in event.content.parts:
                        if part.inline_data and part.inline_data.mime_type.startswith("audio/pcm"):
                            audio_data = part.inline_data.data
                            encoded_audio = base64.b64encode(audio_data).decode("ascii")
                            message_to_send["parts"].append({"type": "audio/pcm", "data": encoded_audio})
                        
                        elif part.function_call:
                            logger.info(f"Tool call: {part.function_call.name}({part.function_call.args})")
                            # Track the tool call
                            tools_called_in_turn.add(part.function_call.name)
                            message_to_send["parts"].append({
                                "type": "function_call", 
                                "data": {
                                    "name": part.function_call.name, 
                                    "args": part.function_call.args or {}
                                }
                            })
                        
                        elif part.function_response:
                            logger.info(f"Tool response: {part.function_response.name} -> {str(part.function_response.response)[:200]}")
                            message_to_send["parts"].append({
                                "type": "function_response",
                                "data": {
                                    "name": part.function_response.name,
                                    "response": part.function_response.response
                                }
                            })
                        

                if (message_to_send["parts"] or 
                    message_to_send["turn_complete"] or
                    message_to_send["interrupted"] or
                    message_to_send["input_transcription"] or
                    message_to_send["output_transcription"]):
                    
                    try:
                        await websocket.send_text(json.dumps(message_to_send))
                    except Exception as send_error:
                        logger.warning(f"Failed to send message to client: {send_error}")
                        break
                    
                    if event.turn_complete:
                        logger.debug("Turn complete")
                    if event.interrupted:
                        logger.info("Agent interrupted by user (barge-in)")

            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"Fatal error in agent_to_client_messaging: {e}", exc_info=True)

async def client_to_agent_messaging(websocket: WebSocket, live_request_queue: LiveRequestQueue):
    """Client to agent communication"""
    logger.info("Client-to-agent messaging started")
    try:
        while True:
            try:
                message_json = await websocket.receive_text()
                message = json.loads(message_json)
                mime_type = message["mime_type"]

                if mime_type == "text/plain":
                    data = message["data"]
                    logger.info(f"Text message received: {data[:100]}" if len(data) > 100 else f"Text message received: {data}")
                    content = Content(role="user", parts=[Part.from_text(text=data)])
                    live_request_queue.send_content(content=content)

                elif mime_type == "audio/pcm":
                    decoded_data = base64.b64decode(message["data"])
                    live_request_queue.send_realtime(Blob(data=decoded_data, mime_type=mime_type))
                    
                else:
                    logger.warning(f"Unsupported mime type: {mime_type}")

            except WebSocketDisconnect:
                logger.info("Client disconnected")
                break

            except Exception as e:
                logger.error(f"Error in client_to_agent_messaging: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Fatal error in client_to_agent_messaging: {e}", exc_info=True)


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
    await websocket.accept()

    user_id_str = user_id if user_id else str(uuid.uuid4())
    logger.info(f"New WebSocket connection: user={user_id_str}, session={session_id or 'new'}")
    
    live_events, live_request_queue, session_id = await start_agent_session(user_id_str, session_id)
    
    # Send session info to client
    await websocket.send_text(json.dumps({
        "session_id": session_id,
        "user_id": user_id_str
    }))
    logger.info(f"Session initialized: {session_id}")

    # Start communication tasks
    agent_to_client_task = asyncio.create_task(
        agent_to_client_messaging(websocket, live_events),
        name="agent_to_client"
    )
    client_to_agent_task = asyncio.create_task(
        client_to_agent_messaging(websocket, live_request_queue),
        name="client_to_agent"
    )

    tasks = [agent_to_client_task, client_to_agent_task]
    
    try:
        # Wait for first task to complete (usually client disconnect)
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        
        # Cancel remaining tasks cleanly
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.debug(f"Task {task.get_name()} cancelled")
    except Exception as e:
        logger.error(f"Error during WebSocket session: {e}", exc_info=True)
    finally:
        # Cleanup
        live_request_queue.close()
        clear_request_context()
        logger.info(f"Connection closed: user={user_id_str}, session={session_id}")
