import { cx } from "class-variance-authority";
import { Edit, Languages } from "lucide-react";
import Image from "next/image";
import React, { useRef, useState } from "react";
import { RTVIClientConfigOption } from "realtime-ai";

import { ClientParams } from "@/components/context";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Field } from "@/components/ui/field";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import {
  LANGUAGES,
  LLM_MODEL_CHOICES,
  TTS_MODEL_CHOICES,
  BOT_PROMPT,
} from "@/rtvi.config";
import { cn } from "@/utils/tailwind";
import { Textarea } from "@/components/ui/textarea";

import StopSecs from "../StopSecs";
import { convertClientParamsToConfigOptions } from "./utils";
import * as Card from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface ConfigSelectProps {
  clientParams: ClientParams;
  onServiceUpdate: (service: { [key: string]: string }) => void;
  onConfigUpdate: (configOption: RTVIClientConfigOption[]) => void;
  language: string;
  setLanguage: (language: string) => void;
  inSession?: boolean;
  showExtra?: boolean;
}

const tileCX = cx(
  "*:opacity-50 cursor-pointer rounded-xl px-4 py-3 bg-white border border-primary-200 bg-white select-none ring-ring transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
);
const tileActiveCX = cx("*:opacity-100 bg-primary-100/70 border-transparent");

export const ConfigSelect: React.FC<ConfigSelectProps> = ({
  onConfigUpdate,
  onServiceUpdate,
  clientParams,
  language,
  setLanguage,
  inSession = false,
  showExtra = false,
}) => {
  const systemPromptModalRef = useRef<HTMLDialogElement>(null);
  const [systemPromptOpen, setSystemPromptOpen] = useState(false);
  const config = convertClientParamsToConfigOptions(clientParams);

  return (
    <>
      <div className="flex flex-col flex-wrap gap-4">
        <Field label="Language" error={false}>
          <Select
            onChange={(e) => {
              const languageConfig = LANGUAGES.find(
                (l) => l.value === e.currentTarget.value
              )!;
              setLanguage(languageConfig.value);
              onServiceUpdate({
                tts: languageConfig.tts_model,
                llm: languageConfig.llm_provider,
                stt: languageConfig.stt_provider,
              });

              onConfigUpdate([
                {
                  service: "tts",
                  options: [
                    { name: "language", value: languageConfig.value },
                    { name: "provider", value: languageConfig.tts_model },
                    { name: "voice", value: languageConfig.default_voice },
                    { name: "model", value: languageConfig.tts_model },
                  ],
                },
                {
                  service: "llm",
                  options: [
                    { name: "model", value: languageConfig.llm_model },
                    { name: "provider", value: languageConfig.llm_provider },
                    {
                      name: "system_prompt",
                      value:
                        BOT_PROMPT[
                          languageConfig.value as keyof typeof BOT_PROMPT
                        ],
                    },
                  ],
                },
                {
                  service: "stt",
                  options: [
                    { name: "model", value: languageConfig.stt_model },
                    { name: "provider", value: languageConfig.stt_provider },
                    { name: "language", value: languageConfig.value },
                  ],
                },
              ]);
            }}
            value={config.tts.language}
            icon={<Languages size={24} />}
          >
            {LANGUAGES.map((lang, i) => (
              <option key={lang.label} value={lang.value}>
                {lang.label}
              </option>
            ))}
          </Select>
        </Field>
        {/* <Accordion type="single" collapsible>
          <AccordionItem value="llm">
            <AccordionTrigger>LLM options</AccordionTrigger>
            <AccordionContent>
              <Field error={false}>
                {!inSession && (
                  <>
                    <Label>Provider</Label>
                    <div className="grid grid-cols-3 gap-2">
                      {LLM_MODEL_CHOICES.map(({ value, label }) => (
                        <div
                          tabIndex={0}
                          className={cn(
                            tileCX,
                            value === config.llm.provider && tileActiveCX
                          )}
                          key={value}
                          onClick={() => {
                            if (value === config.llm.provider) return;

                            const defaultProviderModel = LLM_MODEL_CHOICES.find(
                              (p) => p.value === value
                            )?.models[0].value!;

                            onServiceUpdate({ llm: value });
                            onConfigUpdate([
                              {
                                service: "llm",
                                options: [
                                  { name: "provider", value: value },
                                  {
                                    name: "model",
                                    value: defaultProviderModel,
                                  },
                                  {
                                    name: "system_prompt",
                                    value: config.llm.system_prompt,
                                  },
                                ],
                              },
                            ]);
                          }}
                        >
                          <Image
                            src={`/logo-${value}.svg`}
                            alt={label}
                            width="200"
                            height="60"
                            className="user-select-none pointer-events-none"
                          />
                        </div>
                      ))}
                    </div>
                  </>
                )}

                <Label>Model</Label>
                <Select
                  onChange={(e) => {
                    onServiceUpdate({ llm: config.llm.provider });
                    onConfigUpdate([
                      {
                        service: "llm",
                        options: [
                          { name: "provider", value: config.llm.provider },
                          { name: "model", value: e.currentTarget.value },
                          {
                            name: "system_prompt",
                            value: config.llm.system_prompt,
                          },
                        ],
                      },
                    ]);
                  }}
                  value={config.llm.model}
                >
                  {LLM_MODEL_CHOICES.find(
                    ({ value }) => value === config.llm.provider
                  )?.models.map(({ value, label }) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </Select>
              </Field>
              {config.llm.provider === "anker" && (
                <div className="flex gap-4 items-center pt-4 cursor-pointer">
                  <Label>Customer</Label>
                  <Input
                    type="text"
                    placeholder="anker"
                    value={config.llm.customer}
                    onChange={(e) => {
                      onConfigUpdate([
                        {
                          service: "llm",
                          options: [
                            { name: "provider", value: config.llm.provider },
                            { name: "model", value: config.llm.model },
                            { name: "customer", value: e.currentTarget.value },
                            {
                              name: "system_prompt",
                              value: config.llm.system_prompt,
                            },
                          ],
                        },
                      ]);
                    }}
                  />
                </div>
              )}
              {showExtra && (
                <>
                  <div
                    className="flex gap-2 items-center pt-4 cursor-pointer"
                    onClick={() => {
                      systemPromptModalRef.current?.showModal();
                      setSystemPromptOpen(true);
                    }}
                  >
                    <Edit size={16} />
                    <span>System prompt</span>
                  </div>
                </>
              )}
            </AccordionContent>
          </AccordionItem>
          <AccordionItem value="tts">
            <AccordionTrigger>TTS options</AccordionTrigger>
            <AccordionContent>
              <Field error={false}>
                <Label>Model</Label>
                <Select
                  onChange={(e) => {
                    const provider = TTS_MODEL_CHOICES.find(({ models }) =>
                      models.find((m) => m.value === e.currentTarget.value)
                    )!;
                    const voice = provider.models.find(
                      (m) => m.value === e.currentTarget.value
                    )!;
                    onServiceUpdate({ tts: provider.value });
                    onConfigUpdate([
                      {
                        service: "tts",
                        options: [
                          { name: "language", value: voice.language },
                          { name: "provider", value: provider.value },
                          { name: "voice", value: voice.value },
                          { name: "model", value: provider.value },
                        ],
                      },
                    ]);
                  }}
                  value={config.tts.voice}
                >
                  {TTS_MODEL_CHOICES.filter(({ models }) =>
                    models.find(({ language: lang }) => lang === language)
                  ).map(({ value, label, models }) => (
                    <optgroup key={value} label={label}>
                      {models
                        .filter(({ language: lang }) => language === lang)
                        .map(({ value, label }) => (
                          <option key={value} value={value}>
                            {label}
                          </option>
                        ))}
                    </optgroup>
                  ))}
                </Select>
              </Field>
            </AccordionContent>
          </AccordionItem>
          <AccordionItem value="voice">
            <AccordionTrigger>VAD config</AccordionTrigger>
            <AccordionContent>
              <StopSecs
                label="Speech start timeout"
                helpText="Timeout (seconds) voice activity detection waits after you start speaking"
                value={config.vad.params.start_secs}
                postfix="s"
                handleChange={(v) => {
                  onConfigUpdate([
                    {
                      service: "vad",
                      options: [
                        {
                          name: "params",
                          value: { ...config.vad.params, start_secs: v },
                        },
                      ],
                    },
                  ]);
                }}
              />
              <StopSecs
                label="Speech stop timeout"
                helpText="Timeout (seconds) voice activity detection waits after you stop speaking"
                value={config.vad.params.stop_secs}
                postfix="s"
                handleChange={(v) => {
                  onConfigUpdate([
                    {
                      service: "vad",
                      options: [
                        {
                          name: "params",
                          value: { ...config.vad.params, stop_secs: v },
                        },
                      ],
                    },
                  ]);
                }}
              />
              <StopSecs
                label="Confidence"
                helpText="Confidence threshold for voice activity detection"
                value={config.vad.params.confidence}
                handleChange={(v) => {
                  onConfigUpdate([
                    {
                      service: "vad",
                      options: [
                        {
                          name: "params",
                          value: { ...config.vad.params, confidence: v },
                        },
                      ],
                    },
                  ]);
                }}
              />
              <StopSecs
                label="Minimum volume"
                helpText="Minimum volume for voice activity detection"
                value={config.vad.params.min_volume}
                handleChange={(v) => {
                  onConfigUpdate([
                    {
                      service: "vad",
                      options: [
                        {
                          name: "params",
                          value: { ...config.vad.params, min_volume: v },
                        },
                      ],
                    },
                  ]);
                }}
              />
            </AccordionContent>
          </AccordionItem>
        </Accordion> */}
      </div>

      <dialog ref={systemPromptModalRef}>
        <Card.Card className="w-svw max-w-full md:max-w-lg lg:max-w-xl">
          <Card.CardHeader>
            <Card.CardTitle>Configuration</Card.CardTitle>
          </Card.CardHeader>
          <Card.CardContent>
            {systemPromptOpen && (
              <Textarea defaultValue={config.llm.system_prompt} rows={20} />
            )}
          </Card.CardContent>
          <Card.CardFooter isButtonArray>
            <Button
              variant="outline"
              onClick={() => {
                systemPromptModalRef.current?.close();
                setSystemPromptOpen(false);
              }}
            >
              Cancel
            </Button>
            <Button
              variant="success"
              onClick={() => {
                const llmConfig = clientParams.config.find(
                  ({ service }) => service === "llm"
                )!;
                const newOptions = [...llmConfig.options];
                const systemPromptIndex = newOptions.findIndex(
                  ({ name }) => name === "system_prompt"
                );
                if (systemPromptIndex !== -1) {
                  newOptions[systemPromptIndex] = {
                    name: "system_prompt",
                    value:
                      systemPromptModalRef.current?.querySelector("textarea")
                        ?.value,
                  };
                } else {
                  newOptions.push({
                    name: "system_prompt",
                    value:
                      systemPromptModalRef.current?.querySelector("textarea")
                        ?.value,
                  });
                }
                onConfigUpdate([
                  {
                    service: "llm",
                    options: newOptions,
                  },
                ]);
                systemPromptModalRef.current?.close();
                setSystemPromptOpen(false);
              }}
            >
              Save
            </Button>
          </Card.CardFooter>
        </Card.Card>
      </dialog>
    </>
  );
};

export default ConfigSelect;
