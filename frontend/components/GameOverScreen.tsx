"use client";

import { useRouter } from "next/navigation";
import { useGame } from "../lib/gameContext";

export default function GameOverScreen() {
  const router = useRouter();
  const { game, reset } = useGame();

  function handleTryAgain() {
    reset();
    router.push("/");
  }

  const stats = game
    ? [
        { label: "Damage\ndealt", value: game.damage_dealt_total },
        { label: "Cards\nplayed", value: game.cards_played },
        { label: "Hints\nused", value: game.help_requests },
      ]
    : [];

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
          You ran out of HP.{"\n"}Every hero falls sometimes!
        </p>

        {/* Stats */}
        <div className="flex gap-4 justify-center">
          {stats.map(({ label, value }) => (
            <div
              key={label}
              className="flex flex-col items-center"
              style={{
                background: "#2a0d26",
                border: "2px solid #6a2020",
                padding: "16px 20px",
              }}
            >
              <span className="font-pixel text-2xl" style={{ color: "#e08080" }}>
                {value}
              </span>
              <span
                className="font-pixel mt-2 text-center leading-loose"
                style={{ fontSize: "0.45rem", color: "var(--px-text-dim)", whiteSpace: "pre-line" }}
              >
                {label}
              </span>
            </div>
          ))}
        </div>

        <button onClick={handleTryAgain} className="px-btn w-full py-4 text-sm">
          ↩ Try Again
        </button>
      </div>
    </div>
  );
}
