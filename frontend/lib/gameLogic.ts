import type { Card } from "./types";

const PLAYER_BASE_HP = 100;
const ENEMY_BASE_HP = 100;
const MAX_ENERGY = 3;

export type GameState = {
  playerHP: number;
  playerMaxHP: number;
  enemyHP: number;
  enemyMaxHP: number;
  enemyDamage: number;
  grade: string;
  floor: number;
  turn: number;
  shield: number;
  energy: number;
  maxEnergy: number;
  wrongAttempts: Record<string, number>;
  hand: Card[];
};

/** Return the initial game state for a new game. */
export function initGame(grade: string): GameState {
  const enemyHP = enemyHpForFloor(1);
  const enemyDamage = enemyDamageForFloor(1);

  return {
    playerHP: PLAYER_BASE_HP,
    playerMaxHP: PLAYER_BASE_HP,
    enemyHP: enemyHP,
    enemyMaxHP: enemyHP,
    enemyDamage: enemyDamage,
    grade,
    floor: 1,
    turn: 1,
    shield: 0,
    energy: MAX_ENERGY,
    maxEnergy: MAX_ENERGY,
    wrongAttempts: {},
    hand: [],
  };
}

function resolveCardEffect(state: GameState, card: Card, effectivePower: number): GameState {
  switch (card.card_type) {
    case "attack":
      const newEnemyHP = Math.max(0, state.enemyHP - effectivePower);
      return { ...state, enemyHP: newEnemyHP };
    case "heal":
      const newPlayerHP = Math.min(state.playerMaxHP, state.playerHP + effectivePower);
      return { ...state, playerHP: newPlayerHP };
    case "shield":
      const newShield = state.shield + effectivePower;
      return { ...state, shield: newShield };
  }
}

export function playCard(state: GameState, card: Card, effectivePower: number): GameState {
  return {
    ...resolveCardEffect(state, card, effectivePower),
    energy: Math.max(0, state.energy - card.energy_cost),
    hand: state.hand.filter((c) => c.card_id !== card.card_id),
    wrongAttempts: { ...state.wrongAttempts },
  };
}

export function resolveEndTurn(state: GameState): GameState {
  return {
    ...state,
    energy: state.maxEnergy,
    shield: 0,
    turn: state.turn + 1,
    enemyDamage: enemyDamageForFloor(state.floor),
    wrongAttempts: {},
  };
}

export function resolveEnemyAttack(state: GameState): GameState {
  const absorbed = Math.min(state.shield, state.enemyDamage);
  const actualDamage = state.enemyDamage - absorbed;

  return {
    ...state,
    playerHP: Math.max(0, state.playerHP - actualDamage),
    shield: state.shield - absorbed,
  };
}

export function endTurn(state: GameState, newHand: Card[]): GameState {
  // If enemy is defeated, skip enemy attack and advance to the next floor
  if (state.enemyHP <= 0) {
    const newFloor = state.floor + 1;
    const newEnemyHp = enemyHpForFloor(newFloor);
    // Restore 50% of HP after defeating enemy
    const newPlayerHP = Math.min(state.playerHP + state.playerMaxHP / 2, state.playerMaxHP);

    return {
      ...resolveEndTurn(state),
      hand: newHand,
      playerHP: newPlayerHP,
      floor: newFloor,
      enemyHP: newEnemyHp,
      enemyMaxHP: newEnemyHp,
    };
  }

  // Enemy attacks before the turn resets
  const afterAttack = resolveEnemyAttack(state);

  return {
    ...resolveEndTurn(afterAttack),
    hand: newHand,
  };
}

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

function compareFractions(sub: string, exp: string): boolean | null {
  const sf = parseFraction(sub);
  const ef = parseFraction(exp);
  if (sf === null || ef === null) return null;
  return sf.num * ef.den === ef.num * sf.den;
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

/** Calculate the greatest common denominator. */
function gcd(a: number, b: number): number {
  return b === 0 ? a : gcd(b, a % b);
}

/** Return the card's effective power after applying penalties. */
export function penalisedPower(basePower: number, wrongAttempts: number): number {
  const wrongs = Math.min(wrongAttempts, 5);
  const reduction = Math.ceil(basePower * 0.1) * wrongs;
  return Math.max(basePower - reduction, Math.ceil(basePower * 0.5));
}

/** Calculate the new enemy HP for the given floor number. */
function enemyHpForFloor(floor: number): number {
  return Math.floor(ENEMY_BASE_HP * Math.pow(1.2, floor - 1));
}

/** Calculate the new enemy damage for the given floor number. */
function enemyDamageForFloor(floor: number): number {
  const scale = Math.pow(1.2, floor - 1);
  const min = Math.round(10 * scale);
  const max = Math.round(20 * scale);
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/** Return true if the player has enough energy to play a card. */
export function canPlayCard(energy: number, card: Card): boolean {
  return energy >= card.energy_cost;
}

/** Return true if the player is dead. */
export function isGameOver(state: GameState): boolean {
  return state.playerHP <= 0;
}
