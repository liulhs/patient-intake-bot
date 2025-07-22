"use client";

import { useEffect, useState } from "react";
import * as Card from "@/components/ui/card";

import { Button } from "@/components/ui/button";

import { ClientParams } from "@/components/context";
import ConfigSelect from "@/components/Setup/ConfigSelect";
import { defaultConfig, defaultServices } from "@/rtvi.config";
import { toast } from "sonner";

export default function Settings({
  clientId,
  showExtra = false,
}: {
  clientId?: string;
  showExtra?: boolean;
}) {
  const [language, setLanguage] = useState("en");
  const [clientParams, setClientParams] = useState<null | ClientParams>(null);

  const onConfigUpdate = (newConfigs: any[]) => {
    setClientParams((prev) => {
      if (!prev) return null;
      const newClientParams = {
        config: [...prev.config],
        services: { ...prev.services },
      };
      for (const service of newConfigs) {
        const serviceIndex = prev?.config.findIndex(
          (c) => c.service === service.service
        );
        if (serviceIndex !== -1) {
          newClientParams.config[serviceIndex] = service;
        }
        if (service.service === "tts") {
          const provider = service.options.find(
            (o: any) => o.name === "provider"
          )!.value;
          newClientParams.services.tts = provider;
        }
        if (service.service === "llm") {
          const provider = service.options.find(
            (o: any) => o.name === "provider"
          )!.value;
          newClientParams.services.llm = provider;
        }
        if (service.service === "stt") {
          const provider = service.options.find(
            (o: any) => o.name === "provider"
          )!.value;
          newClientParams.services.stt = provider;
        }
      }
      return newClientParams;
    });
  };

  useEffect(() => {
    async function fetchCallSettings() {
      const callSettings = await getCallSettings(clientId);
      if (!callSettings.config) {
        setClientParams({
          config: defaultConfig,
          services: defaultServices,
        });
      } else {
        setClientParams(callSettings);
      }
    }
    fetchCallSettings();
  }, []);

  const handleSave = () => {
    updateCallSettings(clientParams, clientId);
    toast.success("Settings saved");
  };

  return (
    <>
      <Card.CardContent stack>
        <section className="flex flex-col flex-wrap gap-3 lg:gap-4">
          {clientParams && (
            <ConfigSelect
              onConfigUpdate={onConfigUpdate}
              onServiceUpdate={() => {}}
              inSession={false}
              clientParams={clientParams}
              language={language}
              setLanguage={setLanguage}
              showExtra={showExtra}
            />
          )}
        </section>
      </Card.CardContent>
      <Card.CardFooter isButtonArray>
        <Button key="start" onClick={handleSave}>
          Save
        </Button>
      </Card.CardFooter>
    </>
  );
}

export async function getCallSettings(clientId: undefined | string) {
  const url = clientId
    ? `/voice-api/twilio/call-settings/${clientId}`
    : "/voice-api/twilio/call-settings";
  const response = await fetch(url);
  return response.json();
}

export async function updateCallSettings(
  settings: any,
  clientId: undefined | string
) {
  const url = clientId
    ? `/voice-api/twilio/call-settings/${clientId}`
    : "/voice-api/twilio/call-settings";
  const response = await fetch(url, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(settings),
  });
  return response.json();
}
