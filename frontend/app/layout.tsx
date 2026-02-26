import type { Metadata } from "next";
import { Press_Start_2P } from "next/font/google";
import "./globals.css";
import { GameProvider } from "../lib/gameContext";
import ParallaxBackground from "../components/ParallaxBackground";

const pixelFont = Press_Start_2P({
  weight: "400",
  variable: "--font-pixel",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "MathQuest",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${pixelFont.variable} antialiased`} style={{ background: "#2a0d26" }}>
        {/* Fixed parallax behind everything */}
        <ParallaxBackground />
        {/* Page content sits above it */}
        <div className="relative" style={{ zIndex: 1 }}>
          <GameProvider>{children}</GameProvider>
        </div>
      </body>
    </html>
  );
}
