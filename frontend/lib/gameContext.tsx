"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
  use,
} from "react";
import type { Card } from "./types";
import {
  type GameState,
  initGame as _initGame,
  playCard as _playCard,
  endTurn as _endTurn,
  isGameOver as _isGameOver,
} from "./gameLogic";
import { ensureSignedIn } from "./firebase";

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
  const [game, setGame] = useState<GameState | null>(null);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setGame(loadGame());
    setHydrated(true);
  }, []);

  const setGameCallback = useCallback(
    // Takes either GameState object, or function that updates GameState
    (updater: GameState | null | ((prev: GameState | null) => GameState | null)) => {
      setGame((prev) => {
        const next = typeof updater === "function" ? updater(prev) : updater;
        saveGame(next);
        return next;
      });
    },
    [],
  );

  return [game, hydrated, setGameCallback] as const;
}

type GameContextValue = {
  game: GameState | null;
  hydrated: boolean;
  initGame: (grade: string, hand: Card[]) => void;
  playCard: (card: Card, effectivePower: number) => void;
  endTurn: (newHand: Card[]) => void;
  recordWrongAttempt: (card_id: string) => void;
  getWrongAttempts: (card_id: string) => number;
  isGameOver: () => boolean;
  reset: () => void;
};

const GameContext = createContext<GameContextValue | null>(null);

export function GameProvider({ children }: { children: ReactNode }) {
  const [game, hydrated, setGame] = usePersistedGame();

  // Ensure every visitor has a Firebase UID
  useEffect(() => {
    ensureSignedIn().catch(() => {
      /* no-op: offline or misconfigured */
    });
  }, []);

  const initGame = useCallback(
    (grade: string, hand: Card[]) => {
      setGame({ ..._initGame(grade), hand });
    },
    [setGame],
  );

  const playCard = useCallback(
    (card: Card, effectivePower: number) => {
      setGame((g) => {
        if (!g) return g;

        return _playCard(g, card, effectivePower);
      });
    },
    [setGame],
  );

  const endTurn = useCallback(
    (newHand: Card[]) => {
      setGame((g) => {
        if (!g) return g;

        return _endTurn(g, newHand);
      });
    },
    [setGame],
  );

  const recordWrongAttempt = useCallback(
    (card_id: string) => {
      setGame((g) => {
        if (!g) return g;

        return {
          ...g,
          wrongAttempts: {
            ...g.wrongAttempts,
            [card_id]: (g.wrongAttempts[card_id] ?? 0) + 1,
          },
        };
      });
    },
    [setGame],
  );

  const getWrongAttempts = useCallback(
    (card_id: string): number => game?.wrongAttempts[card_id] ?? 0,
    [game],
  );

  const isGameOver = useCallback((): boolean => _isGameOver(game!), [game]);

  const reset = useCallback(() => setGame(null), [setGame]);

  return (
    <GameContext.Provider
      value={{
        game,
        hydrated,
        initGame,
        playCard,
        endTurn,
        recordWrongAttempt,
        getWrongAttempts,
        isGameOver,
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
