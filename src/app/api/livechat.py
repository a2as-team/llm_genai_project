import json
import asyncio
import base64
import logging
import os
from typing import Optional

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

router = APIRouter(tags=["LiveChat"])
logger = logging.getLogger(__name__)

db_session_service = DatabaseSessionService(
    db_url=database_settings.dsn,
)

async def start_agent_session(user_id: str, session_id: Optional[str] = None):
    """Starts an agent session"""

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
                start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_LOW,
                end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
                prefix_padding_ms=100,
                silence_duration_ms=200,
            )
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
        # Enable transcription for agent's speech output
        output_audio_transcription=types.AudioTranscriptionConfig(),
        # Enable transcription for user's speech input
        input_audio_transcription=types.AudioTranscriptionConfig(),
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
    print("Starting agent to client messaging")
    try:
        async for event in live_events:
            try:
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
                        print(f"User transcription: {transcription_text}")
                        message_to_send["input_transcription"] = {
                            "text": transcription_text,
                            "is_final": not event.partial
                        }
                
                else:
                    if transcription_text:
                        print(f"Model text response: {transcription_text}")
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
                            logger.info(f"Function call: {part.function_call.name}")
                            message_to_send["parts"].append({
                                "type": "function_call", 
                                "data": {
                                    "name": part.function_call.name, 
                                    "args": part.function_call.args or {}
                                }
                            })
                        
                        elif part.function_response:
                            logger.info(f"Function response: {part.function_response.name}")
                            message_to_send["parts"].append({
                                "type": "function_response", 
                                "data": {
                                    "name": part.function_response.name, 
                                    "response": part.function_response.response or {}
                                }
                            })

                if (message_to_send["parts"] or 
                    message_to_send["turn_complete"] or
                    message_to_send["interrupted"] or
                    message_to_send["input_transcription"] or
                    message_to_send["output_transcription"]):
                    
                    await websocket.send_text(json.dumps(message_to_send))

            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"Error in agent_to_client_messaging loop: {e}", exc_info=True)

async def client_to_agent_messaging(websocket: WebSocket, live_request_queue: LiveRequestQueue):
    """Client to agent communication"""
    while True:
        try:
            message_json = await websocket.receive_text()
            message = json.loads(message_json)
            mime_type = message["mime_type"]

            if mime_type == "text/plain":
                data = message["data"]
                content = Content(role="user", parts=[Part.from_text(text=data)])
                live_request_queue.send_content(content=content)

            elif mime_type == "audio/pcm":
                data = message["data"]
                decoded_data = base64.b64decode(data)
                live_request_queue.send_realtime(Blob(data=decoded_data, mime_type=mime_type))

            elif mime_type == "image/jpeg":
                data = message["data"]
                decoded_data = base64.b64decode(data)
                live_request_queue.send_realtime(Blob(data=decoded_data, mime_type=mime_type))
                
            else:
                logger.warning(f"Mime type not supported: {mime_type}")

        except WebSocketDisconnect:
            logger.info("Client disconnected (WebSocketDisconnect).")
            break

        except Exception as e:
            logger.error(f"An error occurred in client_to_agent_messaging: {e}")


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, session_id: Optional[str] = None):
    """Client websocket endpoint"""

    # Wait for client connection
    await websocket.accept()

    # Start agent session
    user_id_str = str(user_id)
    print(user_id_str)
    live_events, live_request_queue, session_id = await start_agent_session(user_id_str, session_id)
    
    # Send session ID to client
    await websocket.send_text(json.dumps({
        "session_id": session_id
    }))

    #debug
    if live_events and live_request_queue:
        print("live etvents and live request queue created")

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
    print(f"Client #{user_id} disconnected")
