"use client";

import { useRouter } from "next/navigation";
import { useGame } from "../lib/gameContext";
import UserProfile from "./UserProfile";

export default function GameOverScreen() {
  const router = useRouter();
  const { reset } = useGame();

  function handleTryAgain() {
    reset();
    router.push("/");
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-8">
      <div
        className="flex flex-col items-center gap-8 w-full max-w-2xl"
        style={{
          background: "var(--px-panel)",
          border: "3px solid #e05050",
          boxShadow: "6px 6px 0 #1d0a1a",
          padding: "48px 40px",
        }}
      >
        <div className="font-pixel text-5xl animate-pixel-pulse">💀</div>

        <h1
          className="font-pixel text-center leading-relaxed"
          style={{
            fontSize: "1.6rem",
            color: "#e05050",
            textShadow: "3px 3px 0 #700000, 5px 5px 0 #1d0a1a",
          }}
        >
          Game Over
        </h1>

        <p
          className="font-pixel text-center text-xs leading-loose"
          style={{ color: "var(--px-text-dim)" }}
        >
          You have been defeated!
        </p>

        <div className="w-full">
          <UserProfile />
        </div>

        <button onClick={handleTryAgain} className="px-btn w-full py-4 text-sm">
          ↩ Try Again
        </button>
      </div>
    </div>
  );
}
