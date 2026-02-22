"use client";

import { useRouter } from "next/navigation";
import { useGame } from "../lib/gameContext";

export default function VictoryScreen() {
  const router = useRouter();
  const { game, reset } = useGame();

  function handlePlayAgain() {
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
        className="flex flex-col items-center gap-8 w-full max-w-lg"
        style={{
          background: "var(--px-panel)",
          border: "3px solid var(--px-gold)",
          boxShadow: "6px 6px 0 #1d0a1a",
          padding: "48px 40px",
        }}
      >
        <div className="font-pixel text-5xl animate-pixel-pulse">🏆</div>

        <h1
          className="font-pixel text-center leading-relaxed"
          style={{
            fontSize: "1.6rem",
            color: "var(--px-gold)",
            textShadow: "3px 3px 0 #7a3d00, 5px 5px 0 #1d0a1a",
          }}
        >
          Victory!
        </h1>

        <p className="font-pixel text-center text-xs leading-loose" style={{ color: "var(--px-text-dim)" }}>
          The enemy has been defeated.{"\n"}You are a math hero!
        </p>

        {/* Stats */}
        <div className="flex gap-4 justify-center">
          {stats.map(({ label, value }) => (
            <div
              key={label}
              className="flex flex-col items-center"
              style={{
                background: "#2a0d26",
                border: "2px solid var(--px-gold-dim)",
                padding: "16px 20px",
              }}
            >
              <span className="font-pixel text-2xl" style={{ color: "var(--px-gold)" }}>
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

        <button onClick={handlePlayAgain} className="px-btn w-full py-4 text-sm">
          ▶ Play Again
        </button>
      </div>
    </div>
  );
}
