import axios from "axios";
import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  try {
    const response = await axios.get(
      `${process.env.NEXT_PUBLIC_BACKEND_URL}/twilio/call-settings`
    );
    return NextResponse.json(response.data);
  } catch (error) {
    console.error("Error handling request:", error);
    return NextResponse.json(
      { error: "Internal Server Error" },
      { status: 500 }
    );
  }
}

export async function PUT(req: NextRequest) {
  try {
    const body = await req.json();
    console.log(body);

    const response = await axios.put(
      `${process.env.NEXT_PUBLIC_BACKEND_URL}/twilio/call-settings`,
      body
    );
    return NextResponse.json(response.data);
  } catch (error) {
    console.error("Error handling request:", error);
    return NextResponse.json((error as any).response.data, { status: 500 });
  }
}
