import type { Card, Difficulty } from "./types";

/** Returns true if the submitted answer matches the expected answer. */
export function checkAnswer(submitted: string, expected: string): boolean {
  const sub = submitted.trim();
  const exp = expected.trim();

  if (sub.toLowerCase() === exp.toLowerCase()) return true;

  // Normalise decimal separator
  const subNorm = sub.replace(",", ".");
  const expNorm = exp.replace(",", ".");

  // Fraction comparison
  const fracResult = compareFractions(subNorm, expNorm);
  if (fracResult !== null) return fracResult;

  // Float comparison
  const subFloat = parseFloat(subNorm);
  const expFloat = parseFloat(expNorm);
  if (!isNaN(subFloat) && !isNaN(expFloat)) {
    return Math.abs(subFloat - expFloat) < 1e-6;
  }

  return false;
}

/** Parse a fraction string like "3/4" into a reduced rational {num, den}. */
function parseFraction(s: string): { num: number; den: number } | null {
  const parts = s.split("/");
  if (parts.length !== 2) return null;
  const num = parseInt(parts[0], 10);
  const den = parseInt(parts[1], 10);
  if (isNaN(num) || isNaN(den) || den === 0) return null;
  const g = gcd(Math.abs(num), Math.abs(den));
  return { num: num / g, den: den / g };
}

function gcd(a: number, b: number): number {
  return b === 0 ? a : gcd(b, a % b);
}

function compareFractions(sub: string, exp: string): boolean | null {
  const sf = parseFraction(sub);
  const ef = parseFraction(exp);
  if (sf === null || ef === null) return null;
  return sf.num * ef.den === ef.num * sf.den;
}

/** Returns the card's effective power after applying wrong-attempt penalties. */
export function penalisedPower(basePower: number, wrongAttempts: number): number {
  const wrongs = Math.min(wrongAttempts, 5);
  const reduction = Math.ceil(basePower * 0.1) * wrongs;
  return Math.max(basePower - reduction, Math.ceil(basePower * 0.5));
}

export type CardEffectResult = {
  enemyHp: number;
  playerHp: number;
  shieldDelta: number; // amount added to shield (0 for attack/heal)
  effectValue: number; // actual power used
};

/**
 * Apply a card's effect to the current game state.
 * @param playerMaxHp - needed to cap heal at max HP
 */
export function applyCard(
  card: Card,
  effectivePower: number,
  enemyHp: number,
  playerHp: number,
  playerMaxHp: number,
): CardEffectResult {
  let newEnemyHp = enemyHp;
  let newPlayerHp = playerHp;
  let shieldDelta = 0;

  switch (card.card_type) {
    case "attack":
      newEnemyHp = Math.max(0, enemyHp - effectivePower);
      break;
    case "heal":
      newPlayerHp = Math.min(playerMaxHp, playerHp + effectivePower);
      break;
    case "shield":
      shieldDelta = effectivePower;
      break;
  }

  return { enemyHp: newEnemyHp, playerHp: newPlayerHp, shieldDelta, effectValue: effectivePower };
}

export type EnemyAttackResult = {
  newPlayerHp: number;
  rawDamage: number;
  absorbed: number;
  actualDamage: number;
};

/**
 * Resolve an enemy attack against the player.
 * @param rawDamage - the pre-rolled damage value stored in game state
 * @param shield    - current shield value
 * @param playerHp  - current player HP
 */
export function resolveEnemyAttack(
  rawDamage: number,
  shield: number,
  playerHp: number,
): EnemyAttackResult {
  const absorbed = Math.min(shield, rawDamage);
  const actualDamage = rawDamage - absorbed;
  const newPlayerHp = Math.max(0, playerHp - actualDamage);
  return { newPlayerHp, rawDamage, absorbed, actualDamage };
}

const ENEMY_BASE_HP = 100;
const ENEMY_BASE_DAMAGE = 15;

/** Calculate the new enemy HP for the given floor number. */
export function enemyHpForFloor(floor: number): number {
  return Math.floor(ENEMY_BASE_HP * Math.pow(1.2, floor - 1));
}

/** Calculate the new enemy damage for the given floor number. */
export function enemyDamageForFloor(floor: number): number {
  const scale = Math.pow(1.2, floor - 1);
  const min = Math.round(10 * scale);
  const max = Math.round(20 * scale);
  return Math.floor(Math.random() * (max - min + 1)) + min;
}
