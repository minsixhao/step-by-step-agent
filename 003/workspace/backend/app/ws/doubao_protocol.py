"""
Doubao / Volcengine Realtime API binary protocol handler.

Frame format (4 bytes header + payload):
- Byte 0: Protocol Version (1)
- Byte 1: Header Size (always 1 for no compression)
- Byte 2: Message Type (0b0001=TextControl, 0b0010=AudioData)
- Byte 3: 0 or 1 (compression flag + reserved)
- Bytes 4+: JSON payload or raw audio data
"""

import struct
import json
import gzip
from enum import IntEnum
from typing import Optional, Tuple


class MessageType(IntEnum):
    TEXT_CONTROL = 0b0001
    AUDIO_DATA = 0b0010


class CompressionType(IntEnum):
    NONE = 0
    GZIP = 1


def pack_frame(msg_type: MessageType, payload: bytes, compress: bool = False) -> bytes:
    """Pack a binary frame according to Doubao protocol."""
    version = 1
    header_size = 1
    compression = CompressionType.GZIP if compress else CompressionType.NONE

    if compress:
        payload = gzip.compress(payload)

    # Byte 3: compression flag in bit 4 (0b00010000)
    byte3 = (compression << 4) | 0

    header = struct.pack("!BBBB", version, header_size, int(msg_type), byte3)
    return header + payload


def unpack_frame(data: bytes) -> Optional[Tuple[MessageType, bytes]]:
    """Unpack a binary frame. Returns (MessageType, payload) or None if incomplete."""
    if len(data) < 4:
        return None

    version = data[0]
    header_size = data[1]
    msg_type = data[2]
    byte3 = data[3]

    compression = (byte3 >> 4) & 0x0F

    if version != 1:
        raise ValueError(f"Unsupported protocol version: {version}")

    payload = data[4:]

    if compression == CompressionType.GZIP:
        payload = gzip.decompress(payload)

    try:
        msg_type_enum = MessageType(msg_type)
    except ValueError:
        raise ValueError(f"Unknown message type: {msg_type}")

    return (msg_type_enum, payload)


def pack_text_control(data: dict) -> bytes:
    """Pack a JSON text control message into a binary frame."""
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return pack_frame(MessageType.TEXT_CONTROL, payload)


def pack_audio_data(audio_bytes: bytes) -> bytes:
    """Pack raw audio data into a binary frame."""
    return pack_frame(MessageType.AUDIO_DATA, audio_bytes)


def unpack_text_control(payload: bytes) -> dict:
    """Unpack a text control payload into a dict."""
    return json.loads(payload.decode("utf-8"))


def create_start_session(
    speaker: str = "vv",
    model_type: str = "dialog",
) -> bytes:
    """Create StartSession message."""
    msg = {
        "type": "StartSession",
        "data": {
            "speaker": speaker,
            "model_type": model_type,
            "app_id": "",
            "access_key": "",
            "resource_id": "volc.speech.dialog",
        }
    }
    return pack_text_control(msg)


def create_finish_session() -> bytes:
    """Create FinishSession message."""
    return pack_text_control({"type": "FinishSession", "data": {}})


def create_finish_connection() -> bytes:
    """Create FinishConnection message."""
    return pack_text_control({"type": "FinishConnection", "data": {}})


def create_end_asr() -> bytes:
    """Create EndASR message."""
    return pack_text_control({"type": "EndASR", "data": {}})


def create_client_interrupt() -> bytes:
    """Create ClientInterrupt message."""
    return pack_text_control({"type": "ClientInterrupt", "data": {}})


def create_update_config(speaker: str) -> bytes:
    """Create UpdateConfig message for changing TTS speaker."""
    return pack_text_control({
        "type": "UpdateConfig",
        "data": {
            "tts": {
                "speaker": speaker,
            }
        }
    })
