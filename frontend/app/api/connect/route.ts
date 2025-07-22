export const runtime = "nodejs"; // Required for SST

import { NextRequest, NextResponse } from "next/server";
import axios from "axios";
import { v4 as uuidv4 } from "uuid";

const DAILY_API_KEY = process.env.DAILY_API_KEY;
const DAILY_API_URL = "https://api.daily.co/v1";
const ANKER_API_URL = process.env.ANKER_API_URL;
const ANKER_API_KEY = process.env.ANKER_API_KEY;

const headers = {
  Authorization: `Bearer ${DAILY_API_KEY}`,
  "Content-Type": "application/json",
};

async function getExistingRooms() {
  try {
    const response = await axios.get(`${DAILY_API_URL}/rooms`, { headers });
    return response.data.data;
  } catch (error) {
    console.error("Error fetching rooms:", error);
    return [];
  }
}

async function checkIfRoomAvailable(roomName: string) {
  try {
    const response = await axios.get(
      `${DAILY_API_URL}/rooms/${roomName}/presence`,
      { headers }
    );
    console.log(response.data);
    return response.data.total_count === 0;
  } catch (error) {
    console.error("Error checking room availability:", error);
    return false;
  }
}

async function createRoom() {
  try {
    const roomName = uuidv4();
    const response = await axios.post(
      `${DAILY_API_URL}/rooms`,
      { name: roomName },
      { headers }
    );
    return response.data;
  } catch (error) {
    console.error("Error creating room:", error);
    return null;
  }
}

async function getARoom() {
  const rooms = await getExistingRooms();
  for (const room of rooms) {
    if (await checkIfRoomAvailable(room.name)) {
      return room;
    }
  }
  return await createRoom();
}

async function getToken(roomName: string, expiryTime = 600, owner = false) {
  try {
    const expiration = Math.floor(Date.now() / 1000) + expiryTime + 20;
    const response = await axios.post(
      `${DAILY_API_URL}/meeting-tokens`,
      {
        properties: {
          room_name: roomName,
          is_owner: owner,
          exp: expiration,
          eject_at_token_exp: true,
          eject_after_elapsed: expiryTime,
        },
      },
      { headers }
    );
    return response.data.token;
  } catch (error) {
    console.error("Error generating token:", error);
    return null;
  }
}

async function startBot(body: any) {
  const response = await axios.post(
    `${process.env.NEXT_PUBLIC_BACKEND_URL}/start`,
    body
  );
  return response.data;
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const room = await getARoom();
    if (!room) {
      return NextResponse.json(
        { error: "Failed to create or get a room" },
        { status: 500 }
      );
    }

    const token = await getToken(room.name);
    if (!token) {
      return NextResponse.json(
        { error: "Failed to generate token" },
        { status: 500 }
      );
    }

    const ttsConfig = body.config.find((c: any) => c.service === "tts");
    const ttsVoice = ttsConfig?.options.find(
      (o: any) => o.name === "voice"
    )?.value;
    const ttsProvider = ttsConfig?.options.find(
      (o: any) => o.name === "model"
    )?.value;

    const llmConfig = body.config.find((c: any) => c.service === "llm");

    const params = {
      room_url: room.url,
      token: token,
      language: ttsConfig?.options.find((o: any) => o.name === "language")
        ?.value,
      tts_model: {
        provider: ttsProvider,
        voice: ttsVoice,
      },
      llm_model: {
        provider: llmConfig?.options.find((o: any) => o.name === "provider")
          ?.value,
        model: llmConfig?.options.find((o: any) => o.name === "model")?.value,
        customer:
          llmConfig?.options.find((o: any) => o.name === "customer")?.value ??
          "anker",
        system_prompt:
          llmConfig?.options.find((o: any) => o.name === "system_prompt")
            ?.value,
      },
      vad_params: body.config
        .find((c: any) => c.service === "vad")
        ?.options.find((o: any) => o.name === "params")?.value,
    };
    console.log("============>", params);
    await startBot(params);

    return NextResponse.json({ room_url: room.url, token });
  } catch (error) {
    console.error("Error handling request:", error);
    return NextResponse.json(
      { error: "Internal Server Error" },
      { status: 500 }
    );
  }
}
