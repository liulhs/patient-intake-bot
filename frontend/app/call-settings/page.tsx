"use client";

import { TooltipProvider } from "@radix-ui/react-tooltip";
import * as Card from "@/components/ui/card";
import Settings from "./components/Settings";
import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

export default function Home() {
  const [settings, setSettings] = useState(null);

  useEffect(() => {
    getCallSettings().then((data) => {
      setSettings(data);
    });
  }, []);

  return (
    <main className="w-full flex items-center justify-center bg-primary-200 p-4 relative">
      <div className="absolute inset-0 bg-[url('/BillingForms_Main.jpg')] bg-no-repeat bg-center bg-cover opacity-30"></div>
      <div id="app" className="relative z-10">
        <TooltipProvider>
          <Card.Card shadow className="animate-appear max-w-lg">
            <Card.CardHeader>
              <Card.CardTitle>Call Settings</Card.CardTitle>
            </Card.CardHeader>
            {settings ? (
              <Settings />
            ) : (
              <div className="flex items-center justify-center h-full">
                <Loader2 className="animate-spin" />
              </div>
            )}
          </Card.Card>
        </TooltipProvider>
      </div>
    </main>
  );
}

async function getCallSettings() {
  const response = await fetch("/voice-api/twilio/call-settings");
  return response.json();
}
