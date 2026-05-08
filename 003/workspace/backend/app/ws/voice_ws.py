"""
WebSocket voice proxy for Doubao Realtime API.
"""

import asyncio
import json
import base64
import struct
import traceback
from typing import Optional

import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from websockets.asyncio.client import connect as ws_connect

from app.core.config import settings
from app.ws.doubao_protocol import (
    pack_frame, unpack_frame, MessageType,
    pack_text_control, pack_audio_data,
    unpack_text_control,
    create_start_session, create_finish_session,
    create_finish_connection, create_end_asr,
    create_client_interrupt, create_update_config,
)

router = APIRouter(tags=["voice"])


async def doubao_connection(speaker: str = "vv"):
    """Create a connection to Doubao Realtime API."""
    headers = {
        "X-Api-App-Id": settings.VOICE_APP_ID,
        "X-Api-Access-Key": settings.VOICE_ACCESS_KEY,
        "X-Api-Resource-Id": settings.VOICE_RESOURCE_ID,
        "X-Api-App-Key": settings.VOICE_APP_KEY,
    }

    ws = await ws_connect(
        settings.VOICE_WS_URL,
        additional_headers=headers,
        ping_interval=20,
        ping_timeout=10,
    )

    # Send StartSession
    await ws.send(create_start_session(speaker=speaker))

    return ws


@router.websocket("/voice/ws")
async def voice_websocket(websocket: WebSocket):
    await websocket.accept()
    print("[Voice] Client connected")

    doubao_ws: Optional[websockets.WebSocketClientProtocol] = None
    speaker = "vv"
    session_started = False

    # Task for forwarding from Doubao to client
    doubao_to_client_task: Optional[asyncio.Task] = None

    async def forward_doubao_to_client():
        """Forward messages from Doubao to the frontend client."""
        nonlocal session_started
        try:
            while doubao_ws:
                try:
                    raw = await asyncio.wait_for(doubao_ws.recv(), timeout=30.0)
                except asyncio.TimeoutError:
                    # Send ping to keep alive
                    if doubao_ws:
                        try:
                            await doubao_ws.ping()
                        except Exception:
                            break
                    continue

                if isinstance(raw, str):
                    # Text message from Doubao - sometimes they send JSON directly
                    try:
                        data = json.loads(raw)
                        msg_type = data.get("type", "Unknown")
                        await websocket.send_json({
                            "type": msg_type,
                            "data": data.get("data", {}),
                        })
                    except json.JSONDecodeError:
                        pass
                elif isinstance(raw, bytes):
                    # Binary frame from Doubao
                    try:
                        msg_type, payload = unpack_frame(raw)
                    except Exception as e:
                        print(f"[Voice] Failed to unpack Doubao frame: {e}")
                        continue

                    if msg_type == MessageType.TEXT_CONTROL:
                        data = unpack_text_control(payload)
                        msg_type_str = data.get("type", "Unknown")

                        if msg_type_str == "StartSessionResponse":
                            session_started = True
                            await websocket.send_json({
                                "type": "SessionStarted",
                                "data": data.get("data", {}),
                            })
                        elif msg_type_str == "TTSResponse":
                            audio_data = data.get("data", {}).get("audio", "")
                            await websocket.send_json({
                                "type": "TTSResponse",
                                "data": audio_data,  # base64 audio
                            })
                        elif msg_type_str == "ASRResponse":
                            await websocket.send_json({
                                "type": "ASRResponse",
                                "data": data.get("data", {}),
                            })
                        elif msg_type_str == "ChatResponse":
                            await websocket.send_json({
                                "type": "ChatResponse",
                                "data": data.get("data", {}),
                            })
                        elif msg_type_str == "FinishSessionResponse":
                            await websocket.send_json({
                                "type": "SessionFinished",
                                "data": {},
                            })
                        else:
                            await websocket.send_json({
                                "type": msg_type_str,
                                "data": data.get("data", {}),
                            })
                    elif msg_type == MessageType.AUDIO_DATA:
                        # Raw audio - send as base64
                        await websocket.send_json({
                            "type": "TTSResponse",
                            "data": base64.b64encode(payload).decode("utf-8"),
                        })

        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"[Voice] Doubao→Client error: {e}")
            traceback.print_exc()

    try:
        while True:
            # Receive message from frontend
            data = await websocket.receive()

            if "text" in data:
                # JSON text message from frontend
                try:
                    msg = json.loads(data["text"])
                    msg_type = msg.get("type", "")
                except json.JSONDecodeError:
                    continue

                if msg_type == "StartSession":
                    # Connect to Doubao
                    speaker = msg.get("data", {}).get("speaker", "vv")
                    if doubao_ws:
                        await doubao_ws.close()
                    doubao_ws = await doubao_connection(speaker=speaker)
                    session_started = False

                    # Start forwarding task
                    if doubao_to_client_task and not doubao_to_client_task.done():
                        doubao_to_client_task.cancel()
                    doubao_to_client_task = asyncio.create_task(forward_doubao_to_client())

                elif msg_type == "FinishSession":
                    if doubao_ws and session_started:
                        await doubao_ws.send(create_finish_session())
                    session_started = False

                elif msg_type == "FinishConnection":
                    if doubao_ws:
                        await doubao_ws.send(create_finish_connection())
                    break

                elif msg_type == "EndASR":
                    if doubao_ws:
                        await doubao_ws.send(create_end_asr())

                elif msg_type == "ClientInterrupt":
                    if doubao_ws:
                        await doubao_ws.send(create_client_interrupt())
                        # Also notify client that interrupt was sent
                        await websocket.send_json({"type": "InterruptAck", "data": {}})

                elif msg_type == "UpdateConfig":
                    new_speaker = msg.get("data", {}).get("tts", {}).get("speaker")
                    if new_speaker and doubao_ws:
                        speaker = new_speaker
                        await doubao_ws.send(create_update_config(new_speaker))

                else:
                    # Generic text control - forward as-is
                    if doubao_ws:
                        await doubao_ws.send(pack_text_control(msg))

            elif "bytes" in data:
                # Binary audio data from frontend
                if doubao_ws:
                    audio_bytes = data["bytes"]
                    await doubao_ws.send(pack_audio_data(audio_bytes))

    except WebSocketDisconnect:
        print("[Voice] Client disconnected")
    except Exception as e:
        print(f"[Voice] Error: {e}")
        traceback.print_exc()
    finally:
        # Cleanup
        if doubao_to_client_task and not doubao_to_client_task.done():
            doubao_to_client_task.cancel()
        if doubao_ws:
            try:
                await doubao_ws.send(create_finish_connection())
                await doubao_ws.close()
            except Exception:
                pass
        try:
            await websocket.close()
        except Exception:
            pass
