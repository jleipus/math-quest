"use client";

import Image from "next/image";
import type { Card as CardInfo, AttackSubtype, Difficulty } from "../lib/types";
import { difficultyColor, difficultyMaterial, cardTypeTheme, asDifficulty } from "../lib/theme";

type Props = {
  card: CardInfo;
  onClick: (card: CardInfo) => void;
  playing: boolean;
  affordable: boolean;
  energyCost: number;
};

function getCardSprite(
  cardType: string,
  attackSubtype: AttackSubtype | null,
  difficulty: Difficulty,
): string {
  const material = difficultyMaterial[difficulty];
  if (cardType === "heal") return "/assets/items/potion.png";
  if (cardType === "shield") return `/assets/items/shields/${material}_shield.png`;
  // attack
  const weapon = attackSubtype === "magic" ? "book" : (attackSubtype ?? "sword");
  if (weapon === "book") return "/assets/items/book.png";
  return `/assets/items/weapons/${material}_${weapon}.png`;
}

export default function Card({ card, onClick, playing, affordable, energyCost }: Props) {
  const theme = cardTypeTheme[card.card_type] ?? cardTypeTheme.attack;
  const diffColor = difficultyColor[asDifficulty(card.task.difficulty)];
  const isDisabled = playing || !affordable;
  const sprite = getCardSprite(
    card.card_type,
    card.attack_subtype ?? null,
    asDifficulty(card.task.difficulty),
  );

  return (
    <button
      onClick={() => {
        if (!isDisabled) onClick(card);
      }}
      disabled={isDisabled}
      title={!affordable ? `Need ${energyCost} energy` : "Click to play"}
      style={{
        width: "clamp(150px, 44vw, 230px)",
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
          padding: "12px 10px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div className="flex items-center gap-2">
          <Image
            src={sprite}
            alt={theme.label}
            width={28}
            height={28}
            style={{ imageRendering: "pixelated" }}
          />
          <span
            className="font-pixel"
            style={{ fontSize: "0.5rem", color: theme.powerColor, letterSpacing: "0.06em" }}
          >
            {theme.label}
          </span>
        </div>

        {/* Energy cost pips */}
        <div className="flex gap-1 items-center">
          {Array.from({ length: energyCost }).map((_, i) => (
            <div
              key={i}
              style={{
                width: 12,
                height: 12,
                background: affordable ? "#f5c842" : "#4a2040",
                border: "1px solid #c89e2a",
              }}
            />
          ))}
        </div>
      </div>

      {/* Body */}
      <div style={{ padding: "10px 10px 0", flex: 1, display: "flex", flexDirection: "column" }}>
        <div className="mb-2 flex items-center gap-2 flex-wrap">
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
          <span
            className="font-pixel"
            style={{
              fontSize: "0.5rem",
              color: "var(--px-text-dim)",
              opacity: 0.8,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
              maxWidth: 120,
            }}
          >
            {card.task.topic}
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
            style={{
              fontSize: "0.58rem",
              color: "var(--px-text-dim)",
              display: "-webkit-box",
              WebkitLineClamp: 3,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
            }}
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
          STY
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
