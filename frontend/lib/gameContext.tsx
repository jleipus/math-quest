"use client";

import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from "react";
import type { Card, StartSessionResponse } from "./types";
import { enemyDamageForFloor } from "./gameLogic";
import { ensureSignedIn } from "./firebase";

type GameState = {
  player_hp: number;
  player_max_hp: number;
  enemy_hp: number;
  enemy_max_hp: number;
  enemy_next_damage: number;
  hand: Card[];
  grade: string;
  floor: number;
  turn: number;
  shield: number;
  energy: number;
  max_energy: number;

  // Per-card wrong-attempt counters (card_id -> count)
  wrong_attempts: Record<string, number>;

  // Stats
  cards_played: number;
  help_requests: number;
};

const STORAGE_KEY = "mathquest_game";

function loadGame(): GameState | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as GameState;
    return null;
  } catch {
    return null;
  }
}

function saveGame(state: GameState | null): void {
  try {
    if (state === null) {
      sessionStorage.removeItem(STORAGE_KEY);
    } else {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    }
  } catch {
    // sessionStorage unavailable, silently ignore
  }
}

function usePersistedGame() {
  const [game, setGameRaw] = useState<GameState | null>(null);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setGameRaw(loadGame());
    setHydrated(true);
  }, []);

  const setGame = useCallback(
    (updater: GameState | null | ((prev: GameState | null) => GameState | null)) => {
      setGameRaw((prev) => {
        const next = typeof updater === "function" ? updater(prev) : updater;
        saveGame(next);
        return next;
      });
    },
    [],
  );

  return [game, hydrated, setGame] as const;
}

type GameContextValue = {
  game: GameState | null;
  hydrated: boolean;
  initGame: (session: StartSessionResponse, grade: string) => void;
  beginTurn: (hand: Card[]) => void;
  setPlayerHp: (hp: number) => void;
  setEnemyHp: (hp: number, maxHp?: number) => void;
  advanceFloor: (enemyHp: number, enemyMaxHp: number, newFloor: number) => void;
  removeCard: (card_id: string) => void;
  addShield: (amount: number) => void;
  spendEnergy: (amount: number) => void;
  recordDamage: (amount: number) => void;
  recordHelp: () => void;
  recordWrongAttempt: (card_id: string) => void;
  getWrongAttempts: (card_id: string) => number;
  reset: () => void;
};

const GameContext = createContext<GameContextValue | null>(null);

export function GameProvider({ children }: { children: ReactNode }) {
  const [game, hydrated, setGame] = usePersistedGame();

  // Ensure every visitor has a Firebase UID (anonymous if not signed in with Google)
  useEffect(() => {
    ensureSignedIn().catch(() => {/* no-op: offline or misconfigured */});
  }, []);

  const initGame = useCallback(
    (session: StartSessionResponse, grade: string) => {
      setGame({
        player_hp: 100,
        player_max_hp: 100,
        enemy_hp: 100,
        enemy_max_hp: 100,
        enemy_next_damage: enemyDamageForFloor(1),
        hand: [],
        grade,
        floor: 1,
        turn: 0,
        shield: 0,
        energy: session.max_energy,
        max_energy: session.max_energy,
        wrong_attempts: {},
        cards_played: 0,
        help_requests: 0,
      });
    },
    [setGame],
  );

  const beginTurn = useCallback(
    (hand: Card[]) => {
      setGame((g) =>
        g
          ? {
              ...g,
              hand,
              energy: g.max_energy,
              shield: 0,
              turn: g.turn + 1,
              enemy_next_damage: enemyDamageForFloor(g.floor),
              wrong_attempts: {},
            }
          : g,
      );
    },
    [setGame],
  );

  const setPlayerHp = useCallback(
    (hp: number) => setGame((g) => (g ? { ...g, player_hp: hp } : g)),
    [setGame],
  );

  const setEnemyHp = useCallback(
    (hp: number, maxHp?: number) => {
      setGame((g) => (g ? { ...g, enemy_hp: hp, enemy_max_hp: maxHp ?? g.enemy_max_hp } : g));
    },
    [setGame],
  );

  const advanceFloor = useCallback(
    (enemyHp: number, enemyMaxHp: number, newFloor: number) => {
      setGame((g) =>
        g ? { ...g, floor: newFloor, enemy_hp: enemyHp, enemy_max_hp: enemyMaxHp } : g,
      );
    },
    [setGame],
  );

  const removeCard = useCallback(
    (card_id: string) => {
      setGame((g) => (g ? { ...g, hand: g.hand.filter((c) => c.card_id !== card_id) } : g));
    },
    [setGame],
  );

  const addShield = useCallback(
    (amount: number) => setGame((g) => (g ? { ...g, shield: g.shield + amount } : g)),
    [setGame],
  );

  const spendEnergy = useCallback(
    (amount: number) => {
      setGame((g) => (g ? { ...g, energy: Math.max(0, g.energy - amount) } : g));
    },
    [setGame],
  );

  const recordDamage = useCallback(
    (_amount: number) => {
      setGame((g) => (g ? { ...g, cards_played: g.cards_played + 1 } : g));
    },
    [setGame],
  );

  const recordHelp = useCallback(() => {
    setGame((g) => (g ? { ...g, help_requests: g.help_requests + 1 } : g));
  }, [setGame]);

  const recordWrongAttempt = useCallback(
    (card_id: string) => {
      setGame((g) => {
        if (!g) return g;
        return {
          ...g,
          wrong_attempts: {
            ...g.wrong_attempts,
            [card_id]: (g.wrong_attempts[card_id] ?? 0) + 1,
          },
        };
      });
    },
    [setGame],
  );

  const getWrongAttempts = useCallback(
    (card_id: string): number => game?.wrong_attempts[card_id] ?? 0,
    [game],
  );

  const reset = useCallback(() => setGame(null), [setGame]);

  return (
    <GameContext.Provider
      value={{
        game,
        hydrated,
        initGame,
        beginTurn,
        setPlayerHp,
        setEnemyHp,
        advanceFloor,
        removeCard,
        addShield,
        spendEnergy,
        recordDamage,
        recordHelp,
        recordWrongAttempt,
        getWrongAttempts,
        reset,
      }}
    >
      {children}
    </GameContext.Provider>
  );
}

export function useGame(): GameContextValue {
  const ctx = useContext(GameContext);
  if (!ctx) throw new Error("useGame must be used inside <GameProvider>");
  return ctx;
}
