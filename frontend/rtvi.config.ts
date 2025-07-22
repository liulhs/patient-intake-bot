export const BOT_READY_TIMEOUT = 15 * 1000; // 15 seconds

export const defaultMaxDuration = 600;

export const BOT_PROMPT = {
  "en": `Role: 
- You are a voice customer service. your task is to select the right tool based on the context to answer user question.
- Answer user questions succinctly and return content less than 100 words.
Style Guide:
Be concise: Stick to one topic per response.
Be conversational: Use natural, friendly language.
Be proactive: Lead the conversation with next-step suggestions.
Clarify when needed: If the user's answer is unclear, ask again.
One thing at a time: Avoid multiple questions in one response.
Response Rules:
Stay in character and keep the dialogue smooth.
If unsure, admit it—don't make up answers.
Guide conversations back to the topic naturally.
Keep responses lively, expressive, and engaging.
Follow these rules:
Numbers & Ordinals: '123' → 'one hundred twenty-three', '1st' → 'first'
Phone Number: use comma to separate different part to ensure there is a stop
URLs: Use uppercase to spell each part clearly, replacing symbols with spoken equivalents:
'www.example.com' → 'www dot example dot COM'
'www.character.ai' → 'www dot character dot AI'
Addresses: Convert numbers to spoken form:
'123 Main St.' → 'one two three Main Street'
'45B 7th Ave.' → 'four five B Seventh Avenue'
Avoid tokenization artifacts: Ensure that words are not split with spaces.

You also have a lively, engaging, and expressive personality. 
Your responses should feel natural, like a human conversation, rather than robotic. 
To achieve this, incorporate:
Interjections (Wow, Ah, Oh no, Whoa)
Emotional modifiers (Super, Kind of, Honestly, Absolutely, No way!)
Casual, conversational phrasing (You know what? To be honest, I did NOT see that coming!)
Respond to what the user said in a creative and helpful way, but keep your responses brief.
Start by introducing yourself.

Respond only in English please.`
}

export const LANGUAGES = [
  {
    label: "English",
    value: "en",
    tts_model: "cartesia",
    default_voice: "156fb8d2-335b-4950-9cb3-a2d33befec77",
    llm_provider: "openai",
    llm_model: "gpt-4o",
    stt_provider: "deepgram",
    stt_model: "nova-3-general",
  }
];

export const defaultServices = {
  llm: "openai",
  tts: "cartesia",
  stt: "deepgram",
};

export const defaultConfig = [
  {
    service: "vad",
    options: [
      {
        name: "params",
        value: {
          start_secs: 0.2,
          stop_secs: 0.8,
          confidence: 1,
          min_volume: 0.6,
        },
      },
    ],
  },
  {
    service: "tts",
    options: [
      { name: "provider", value: LANGUAGES[0].tts_model },
      { name: "voice", value: LANGUAGES[0].default_voice },
      { name: "model", value: LANGUAGES[0].tts_model },
      { name: "language", value: LANGUAGES[0].value },
    ],
  },
  {
    service: "llm",
    options: [
      { name: "provider", value: "anker" },
      { name: "model", value: "anker-prod" },
      { name: "system_prompt", value: BOT_PROMPT["en"] },
      { name: "run_on_config", value: true },
    ],
  },
  {
    service: "stt",
    options: [
      { name: "provider", value: LANGUAGES[0].stt_provider },
      { name: "model", value: LANGUAGES[0].stt_model },
      { name: "language", value: LANGUAGES[0].value },
    ],
  },
];

export const LLM_MODEL_CHOICES = [
  {
    label: "OpenAI",
    value: "openai",
    models: [
      {
        label: "GPT-4o",
        value: "gpt-4o",
      },
      {
        label: "GPT-4o Mini",
        value: "gpt-4o-mini",
      },
    ],
  },
];

export const TTS_MODEL_CHOICES = [
  {
    label: "Cartesia",
    value: "cartesia",
    models: [
      {
        label: "Jacqueline (F)",
        value: "9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        language: "en",
      },
      {
        label: "Brooke (F)",
        value: "6f84f4b8-58a2-430c-8c79-688dad597532",
        language: "en",
      },
      {
        label: "Jordan (M)",
        value: "87bc56aa-ab01-4baa-9071-77d497064686",
        language: "en",
      },
      {
        label: "Vexa (F)",
        value: "156fb8d2-335b-4950-9cb3-a2d33befec77",
        language: "en",
      },
      {
        label: "Chongz (M)",
        value: "146485fd-8736-41c7-88a8-7cdd0da34d84",
        language: "en",
      },
      {
        label: "Keith (M)",
        value: "9fa83ce3-c3a8-4523-accc-173904582ced",
        language: "en",
      },
      {
        label: "Ronald (M)",
        value: "5ee9feff-1265-424a-9d7f-8e4d431a12c7",
        language: "en",
      },
      {
        label: "Salesman (M)",
        value: "820a3788-2b37-4d21-847a-b65d8a68c99a",
        language: "en",
      },
      {
        label: "Joan (F)",
        value: "5abd2130-146a-41b1-bcdb-974ea8e19f56",
        language: "en",
      },
      {
        label: "Connie (F)",
        value: "8d8ce8c9-44a4-46c4-b10f-9a927b99a853",
        language: "en",
      },
      {
        label: "Professional women (F)",
        value: "248be419-c632-4f23-adf1-5324ed7dbf1d",
        language: "en",
      },
      {
        label: "教授",
        value: "c59c247b-6aa9-4ab6-91f9-9eabea7dc69e",
        language: "zh",
      },
      {
        label: "接线员",
        value: "3a63e2d1-1c1e-425d-8e79-5100bc910e90",
        language: "zh",
      },
      {
        label: "Kenji (M)",
        value: "6b92f628-be90-497c-8f4c-3b035002df71",
        language: "ja",
      },
      {
        label: "Yuki (F)",
        value: "59d4fd2f-f5eb-4410-8105-58db7661144f",
        language: "ja",
      },
      {
        label: "Yumi (F)",
        value: "2b568345-1d48-4047-b25f-7baccf842eb0",
        language: "ja",
      },
      {
        label: "Yuto (M)",
        value: "e8a863c6-22c7-4671-86ca-91cacffc038d",
        language: "ja",
      },
    ],
  },
];
