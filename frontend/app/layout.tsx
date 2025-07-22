import type { Metadata } from "next";
import { Inter, Space_Mono } from "next/font/google";

import "./global.css";
import { Toaster } from "sonner";

// Font
const fontSans = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-sans",
});

const fontMono = Space_Mono({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "Audio Bots Demo",
  description: "Audio Bots voice-to-voice example app",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${fontSans.variable} ${fontMono.variable}`}>
        <Toaster richColors position="top-center" />
        {children}
      </body>
    </html>
  );
}
