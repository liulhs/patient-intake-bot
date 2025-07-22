import { Book, Info } from "lucide-react";
import React from "react";

import { Button } from "./ui/button";

type SplashProps = {
  handleReady: () => void;
};

export const Splash: React.FC<SplashProps> = ({ handleReady }) => {
  return (
    <main className="w-full flex items-center justify-center bg-primary-200 p-4 relative">
      <div className="absolute inset-0 bg-[url('/BillingForms_Main.jpg')] bg-no-repeat bg-center bg-cover opacity-30"></div>
      <div className="flex flex-col gap-8 lg:gap-12 items-center max-w-full lg:max-w-3xl relative z-10">
        <h1 className="scroll-m-20 text-4xl font-extrabold tracking-tight lg:text-5xl text-balance text-center">
          Newcast Workflow Voice Agent Demo
        </h1>

        <Button onClick={() => handleReady()}>Talk to a Patient Intake Agent now</Button>


        <footer className="flex flex-col lg:gap-2">
          <Button variant="light" asChild>
            <a
              href="https://calendly.com/newcast/30min"
              className="text-indigo-600"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Info className="size-6" />
              Learn more about Newcast Interactive AI Agents
            </a>
          </Button>
        </footer>
      </div>
    </main>
  );
};

export default Splash;
