#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""RTVI Bot Server Implementation.

This FastAPI server manages RTVI bot instances and provides endpoints for both
direct browser access and RTVI client connections. It handles:
- Creating Daily rooms
- Managing bot processes
- Providing connection credentials
- Monitoring bot status

Requirements:
- Daily API key (set in .env file)
- Python 3.10+
- FastAPI
- Running bot implementation
"""

import argparse
import os
import subprocess
from contextlib import asynccontextmanager
from typing import Any, Dict

import aiohttp
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from typing import Optional
import json

from pipecat.transports.services.helpers.daily_rest import DailyRESTHelper, DailyRoomParams

# Load environment variables from .env file
load_dotenv(override=True)

# Maximum number of bot instances allowed per room
MAX_BOTS_PER_ROOM = 1

# Dictionary to track bot processes: {pid: (process, room_url)}
bot_procs = {}

# Store Daily API helpers
daily_helpers = {}


def cleanup():
    """Cleanup function to terminate all bot processes.

    Called during server shutdown.
    """
    for entry in bot_procs.values():
        proc = entry[0]
        proc.terminate()
        proc.wait()


def get_bot_file():
    bot_implementation = os.getenv("BOT_IMPLEMENTATION", "openai").lower().strip()
    # If blank or None, default to openai
    if not bot_implementation:
        bot_implementation = "openai"
    if bot_implementation not in ["openai", "gemini"]:
        raise ValueError(
            f"Invalid BOT_IMPLEMENTATION: {bot_implementation}. Must be 'openai' or 'gemini'"
        )
    return f"bot-{bot_implementation}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan manager that handles startup and shutdown tasks.

    - Creates aiohttp session
    - Initializes Daily API helper
    - Cleans up resources on shutdown
    """
    aiohttp_session = aiohttp.ClientSession()
    daily_helpers["rest"] = DailyRESTHelper(
        daily_api_key=os.getenv("DAILY_API_KEY", ""),
        daily_api_url=os.getenv("DAILY_API_URL", "https://api.daily.co/v1"),
        aiohttp_session=aiohttp_session,
    )
    yield
    await aiohttp_session.close()
    cleanup()


# Initialize FastAPI app with lifespan manager
app = FastAPI(
    title="OpenAI Voice Agent API",
    description="API for the OpenAI Voice Agent",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def create_room_and_token() -> tuple[str, str]:
    """Helper function to create a Daily room and generate an access token.
    
    First tries to use environment variables for room URL and token.
    If not available, creates a new room.

    Returns:
        tuple[str, str]: A tuple containing (room_url, token)

    Raises:
        HTTPException: If room creation or token generation fails
    """
    # First try to use environment variables
    room_url = os.getenv("DAILY_SAMPLE_ROOM_URL")
    token = os.getenv("DAILY_SAMPLE_ROOM_TOKEN")
    
    if room_url and token:
        print(f"Using existing room from environment: {room_url}")
        return room_url, token
        
    # If no room URL in env, create a new room
    print("Creating new Daily room...")
    try:
        room = await daily_helpers["rest"].create_room(DailyRoomParams())
        if not room.url:
            raise Exception("No URL in room creation response")
            
        room_url = room.url
        print(f"Created new room: {room_url}")
        
        # Get token for the new room
        token = await daily_helpers["rest"].get_token(room_url)
        if not token:
            raise Exception(f"Failed to get token for room: {room_url}")
            
        print(f"Got token for room: {room_url}")
        return room_url, token
        
    except Exception as e:
        print(f"Error creating room: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create room: {str(e)}"
        )


@app.post("/start")
async def start_agent(request: Request):
    """Endpoint for starting a voice agent session.

    Creates or uses an existing Daily room and starts a bot instance.

    Request Body:
        JSON object with room_url, token, and configuration

    Returns:
        JSON: Room URL and token for the session

    Raises:
        HTTPException: If room creation, token generation, or bot startup fails
    """
    try:
        data = await request.json()
        print(f"Received start request with data: {json.dumps(data, indent=2)}")
        
        # Use provided room_url and token or create new ones
        room_url = data.get("room_url") or os.getenv("DAILY_SAMPLE_ROOM_URL")
        token = data.get("token") or os.getenv("DAILY_SAMPLE_ROOM_TOKEN")
        
        if not room_url or not token:
            # Fall back to creating a new room if env vars not set
            room_url, token = await create_room_and_token()
            
        print(f"Using room URL: {room_url}")

        # Check if there is already an existing process running in this room
        num_bots_in_room = sum(
            1 for proc in bot_procs.values() if proc[1] == room_url and proc[0].poll() is None
        )
        if num_bots_in_room >= MAX_BOTS_PER_ROOM:
            return JSONResponse(
                status_code=400,
                content={"error": f"Max bot limit reached for room: {room_url}"}
            )

        # Start the bot process with configuration from the request
        try:
            bot_file = get_bot_file()
            cmd = [
                "python3", "-m", bot_file,
                "--url", room_url,
                "--token", token,
                "--language", data.get("language", "en"),
                "--llm-provider", "openai"  # Force OpenAI provider
            ]
            
            # Add TTS voice if provided
            if "tts_model" in data and "voice" in data["tts_model"]:
                cmd.extend(["--tts-voice", data["tts_model"]["voice"]])
                
            print(f"Starting bot with command: {' '.join(cmd)}")
            
            proc = subprocess.Popen(
                cmd,
                cwd=os.path.dirname(os.path.abspath(__file__)),
            )
            bot_procs[proc.pid] = (proc, room_url)
            
            return {
                "room_url": room_url,
                "token": token,
                "bot_pid": proc.pid
            }
            
        except Exception as e:
            print(f"Failed to start bot: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Failed to start bot: {str(e)}"}
            )
            
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON payload"}
        )
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal server error: {str(e)}"}
        )


@app.post("/connect")
async def rtvi_connect(request: Request) -> Dict[Any, Any]:
    """RTVI connect endpoint that creates a room and returns connection credentials.

    This endpoint is called by RTVI clients to establish a connection.
    It expects a JSON body with the following structure:
    {
        "services": {
            "llm": "openai",
            "tts": "cartesia",
            "stt": "deepgram"
        },
        "config": [...]
    }

    Returns:
        Dict[Any, Any]: Authentication bundle containing room_url and token

    Raises:
        HTTPException: If room creation, token generation, or bot startup fails
    """
    try:
        data = await request.json()
        print(f"Received connect request with data: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"Error parsing request data: {e}")
        data = {}

    print("Creating room for RTVI connection")
    room_url, token = await create_room_and_token()
    print(f"Room URL: {room_url}")

    # Start the bot process
    try:
        bot_file = get_bot_file()
        cmd = [
            "python3", "-m", bot_file,
            "--url", room_url,
            "--token", token,
            "--language", "en"  # Default to English
        ]
        
        # Add additional parameters from the request if available
        if data and "config" in data:
            for config in data["config"]:
                if config["service"] == "llm" and "model" in config:
                    cmd.extend(["--llm-model", config["model"]])
                elif config["service"] == "tts" and "voice" in config:
                    cmd.extend(["--tts-voice", config["voice"]])

        print(f"Starting bot with command: {' '.join(cmd)}")
        
        proc = subprocess.Popen(
            cmd,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        bot_procs[proc.pid] = (proc, room_url)
    except Exception as e:
        print(f"Failed to start bot: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start bot: {str(e)}"
        )

    # Return the authentication bundle in format expected by DailyTransport
    return {
        "room_url": room_url,
        "token": token,
        "bot_pid": proc.pid
    }


@app.get("/status/{pid}")
def get_status(pid: int):
    """Get the status of a specific bot process.

    Args:
        pid (int): Process ID of the bot

    Returns:
        JSONResponse: Status information for the bot

    Raises:
        HTTPException: If the specified bot process is not found
    """
    # Look up the subprocess
    proc = bot_procs.get(pid)

    # If the subprocess doesn't exist, return an error
    if not proc:
        raise HTTPException(status_code=404, detail=f"Bot with process id: {pid} not found")

    # Check the status of the subprocess
    status = "running" if proc[0].poll() is None else "finished"
    return JSONResponse({"bot_id": pid, "status": status})


@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication with the frontend"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back the received message
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


if __name__ == "__main__":
    import uvicorn

    # Parse command line arguments for server configuration
    default_host = os.getenv("HOST", "0.0.0.0")
    default_port = int(os.getenv("FAST_API_PORT", "17860")) # Switch to 18860 for local
    default_log_level = os.getenv("LOG_LEVEL", "info")

    parser = argparse.ArgumentParser(description="OpenAI Voice Agent FastAPI server")
    parser.add_argument("--host", type=str, default=default_host, help="Host address")
    parser.add_argument("--port", type=int, default=default_port, help="Port number")
    parser.add_argument("--reload", action="store_true", help="Reload code on change")
    parser.add_argument("--log-level", type=str, default=default_log_level,
                      choices=["critical", "error", "warning", "info", "debug", "trace"],
                      help="Log level")

    args = parser.parse_args()

    # Start the FastAPI server
    uvicorn.run(
        "server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
        # Required for WebSocket support
        ws_ping_interval=20,
        ws_ping_timeout=20,
        timeout_keep_alive=60,
    )
