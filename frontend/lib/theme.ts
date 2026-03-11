import type { CardType, Difficulty } from "./types";

export const difficultyColor: Record<Difficulty, string> = {
  easy: "#4caf50",
  medium: "#f5c842",
  hard: "#e05050",
};

/** Sprite material name used for card artwork. */
export const difficultyMaterial: Record<Difficulty, string> = {
  easy: "wooden",
  medium: "iron",
  hard: "gold",
};

/**
 * Health-bar / accuracy-bar colour based on a 0–1 fraction.
 * ≥ 0.7 → green, ≥ 0.4 → yellow, < 0.4 → red.
 */
export function fractionColor(fraction: number): string {
  if (fraction >= 0.7) return difficultyColor.easy;
  if (fraction >= 0.4) return difficultyColor.medium;
  return difficultyColor.hard;
}

export type CardTypeTheme = {
  bg: string;
  border: string;
  headerBg: string;
  label: string;
  powerBg: string;
  powerColor: string;
  glowColor: string;
  /** Colour used for floating damage/heal/shield numbers in battle. */
  floatColor: string;
};

export const cardTypeTheme: Record<CardType, CardTypeTheme> = {
  attack: {
    bg: "#280a0a",
    border: "#c05030",
    headerBg: "#4a1010",
    label: "ATTACK",
    powerBg: "#c05030",
    powerColor: "#fff0ee",
    glowColor: "rgba(200,80,50,0.45)",
    floatColor: "#e05050",
  },
  heal: {
    bg: "#0a1f0e",
    border: "#3a8a50",
    headerBg: "#0e3518",
    label: "HEAL",
    powerBg: "#2a7a40",
    powerColor: "#e0ffe8",
    glowColor: "rgba(60,180,80,0.4)",
    floatColor: "#4caf50",
  },
  shield: {
    bg: "#0a0e28",
    border: "#4060b0",
    headerBg: "#101840",
    label: "SHIELD",
    powerBg: "#2a4090",
    powerColor: "#dde8ff",
    glowColor: "rgba(80,120,220,0.45)",
    floatColor: "#6080d0",
  },
};
