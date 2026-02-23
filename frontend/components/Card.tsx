"use client";

import type { Card as CardType, CardType as CardTypeValue, Difficulty } from "../lib/types";

type Props = {
  card: CardType;
  index: number; // 1-based keyboard shortcut hint
  onClick: (card: CardType) => void;
  playing: boolean;
  affordable: boolean;
  energyCost: number;
};

const difficultyColor: Record<Difficulty, string> = {
  easy: "#4caf50",
  medium: "#f5c842",
  hard: "#e05050",
};

const cardTypeTheme: Record<
  CardTypeValue,
  {
    bg: string;
    border: string;
    headerBg: string;
    icon: string;
    label: string;
    powerBg: string;
    powerColor: string;
    glowColor: string;
  }
> = {
  attack: {
    bg: "#280a0a",
    border: "#c05030",
    headerBg: "#4a1010",
    icon: "⚔️",
    label: "ATTACK",
    powerBg: "#c05030",
    powerColor: "#fff0ee",
    glowColor: "rgba(200,80,50,0.45)",
  },
  heal: {
    bg: "#0a1f0e",
    border: "#3a8a50",
    headerBg: "#0e3518",
    icon: "💚",
    label: "HEAL",
    powerBg: "#2a7a40",
    powerColor: "#e0ffe8",
    glowColor: "rgba(60,180,80,0.4)",
  },
  shield: {
    bg: "#0a0e28",
    border: "#4060b0",
    headerBg: "#101840",
    icon: "🛡️",
    label: "SHIELD",
    powerBg: "#2a4090",
    powerColor: "#dde8ff",
    glowColor: "rgba(80,120,220,0.45)",
  },
};

export default function Card({ card, index, onClick, playing, affordable, energyCost }: Props) {
  const theme = cardTypeTheme[card.card_type] ?? cardTypeTheme.attack;
  const diffColor = difficultyColor[card.task.difficulty];
  const isDisabled = playing || !affordable;

  return (
    <button
      onClick={() => {
        if (!isDisabled) onClick(card);
      }}
      disabled={isDisabled}
      title={!affordable ? `Need ${energyCost} energy` : "Click to play"}
      style={{
        width: 172,
        minHeight: 264,
        background: theme.bg,
        border: `3px solid ${theme.border}`,
        boxShadow: affordable
          ? `4px 4px 0 #0a0008, 0 0 22px ${theme.glowColor}`
          : "4px 4px 0 #0a0008",
        display: "flex",
        flexDirection: "column",
        padding: 0,
        textAlign: "left",
        cursor: isDisabled ? "not-allowed" : "pointer",
        opacity: isDisabled ? 0.4 : 1,
        transition: "transform 0.1s, box-shadow 0.1s",
        imageRendering: "pixelated",
        overflow: "hidden",
      }}
      onMouseEnter={(e) => {
        if (!isDisabled)
          (e.currentTarget as HTMLButtonElement).style.transform = "translateY(-8px)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLButtonElement).style.transform = "translateY(0)";
      }}
    >
      {/* Header band */}
      <div
        style={{
          background: theme.headerBg,
          borderBottom: `2px solid ${theme.border}`,
          padding: "8px 10px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div className="flex items-center gap-1">
          <span style={{ fontSize: 14 }}>{theme.icon}</span>
          <span
            className="font-pixel"
            style={{ fontSize: "0.5rem", color: theme.powerColor, letterSpacing: "0.06em" }}
          >
            {theme.label}
          </span>
        </div>

        {/* Keyboard shortcut badge */}
        <span
          className="font-pixel"
          style={{
            fontSize: "0.5rem",
            background: "rgba(0,0,0,0.45)",
            border: "1px solid rgba(255,255,255,0.15)",
            color: affordable ? "rgba(255,255,255,0.7)" : "rgba(255,255,255,0.25)",
            padding: "1px 5px",
          }}
        >
          {index}
        </span>

        {/* Energy cost pips */}
        <div className="flex gap-1 items-center">
          {Array.from({ length: energyCost }).map((_, i) => (
            <div
              key={i}
              style={{
                width: 8,
                height: 8,
                background: affordable ? "#f5c842" : "#4a2040",
                border: "1px solid #c89e2a",
              }}
            />
          ))}
        </div>
      </div>

      {/* Body */}
      <div style={{ padding: "10px 10px 0", flex: 1, display: "flex", flexDirection: "column" }}>
        <div className="mb-2">
          <span
            className="font-pixel"
            style={{
              fontSize: "0.5rem",
              background: diffColor,
              color: "#0a0008",
              padding: "2px 6px",
            }}
          >
            {card.task.difficulty.toUpperCase()}
          </span>
        </div>

        <div
          className="font-pixel mb-2 leading-snug"
          style={{ fontSize: "0.65rem", color: theme.powerColor }}
        >
          {card.card_name}
        </div>

        <div className="flex-1">
          <p
            className="font-pixel leading-relaxed"
            style={{ fontSize: "0.58rem", color: "var(--px-text-dim)" }}
          >
            {card.task.question}
          </p>
        </div>
      </div>

      {/* Bottom bar */}
      <div
        style={{
          background: theme.headerBg,
          borderTop: `2px solid ${theme.border}`,
          padding: "6px 10px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <span className="font-pixel" style={{ fontSize: "0.5rem", color: "var(--px-text-dim)" }}>
          PWR
        </span>
        <span
          className="font-pixel flex items-center justify-center"
          style={{
            width: 36,
            height: 36,
            background: theme.powerBg,
            color: theme.powerColor,
            fontSize: "0.8rem",
            border: `2px solid ${theme.border}`,
          }}
        >
          {card.card_power}
        </span>
      </div>
    </button>
  );
}
