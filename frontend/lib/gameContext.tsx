"use client";

import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import type { Card, InitGameResponse } from "./types";
import { MAX_ENERGY } from "./types";

type GameState = {
  session_id: string;
  player_hp: number;
  player_max_hp: number;
  enemy_hp: number;
  enemy_max_hp: number;
  enemy_next_damage: number;
  hand: Card[];
  topic: string;
  floor: number;
  shield: number;
  energy: number;
  max_energy: number;
  damage_dealt_total: number;
  cards_played: number;
  help_requests: number;
};

type GameContextValue = {
  game: GameState | null;
  initGame: (session: InitGameResponse, topic: string, maxHp: number) => void;
  setHand: (hand: Card[], enemyNextDamage: number) => void;
  unlockCard: (card_id: string) => void;
  setPlayerHp: (hp: number) => void;
  setEnemyHp: (hp: number) => void;
  removeCard: (card_id: string) => void;
  addShield: (amount: number) => void;
  spendEnergy: (amount: number) => void;
  recordDamage: (amount: number) => void;
  recordHelp: () => void;
  spawnNextFloor: (floor: number, enemyHp: number, enemyMaxHp: number, enemyNextDamage: number) => void;
  reset: () => void;
};

const GameContext = createContext<GameContextValue | null>(null);

export function GameProvider({ children }: { children: ReactNode }) {
  const [game, setGame] = useState<GameState | null>(null);

  const initGame = useCallback(
    (session: InitGameResponse, topic: string, maxHp: number) => {
      setGame({
        session_id: session.session_id,
        player_hp: session.player_hp,
        player_max_hp: maxHp,
        enemy_hp: session.enemy_hp,
        enemy_max_hp: session.enemy_hp,
        enemy_next_damage: 0,
        hand: [],
        topic,
        floor: session.floor ?? 1,
        shield: 0,
        energy: MAX_ENERGY,
        max_energy: MAX_ENERGY,
        damage_dealt_total: 0,
        cards_played: 0,
        help_requests: 0,
      });
    },
    [],
  );

  const setHand = useCallback((hand: Card[], enemyNextDamage: number) => {
    setGame((g) =>
      g ? { ...g, hand, energy: MAX_ENERGY, enemy_next_damage: enemyNextDamage, shield: 0 } : g,
    );
  }, []);

  const unlockCard = useCallback((card_id: string) => {
    setGame((g) =>
      g
        ? { ...g, hand: g.hand.map((c) => (c.card_id === card_id ? { ...c, locked: false } : c)) }
        : g,
    );
  }, []);

  const setPlayerHp = useCallback((hp: number) => {
    setGame((g) => (g ? { ...g, player_hp: hp } : g));
  }, []);

  const setEnemyHp = useCallback((hp: number) => {
    setGame((g) => (g ? { ...g, enemy_hp: hp } : g));
  }, []);

  const removeCard = useCallback((card_id: string) => {
    setGame((g) => (g ? { ...g, hand: g.hand.filter((c) => c.card_id !== card_id) } : g));
  }, []);

  const addShield = useCallback((amount: number) => {
    setGame((g) => (g ? { ...g, shield: g.shield + amount } : g));
  }, []);

  const spendEnergy = useCallback((amount: number) => {
    setGame((g) => (g ? { ...g, energy: Math.max(0, g.energy - amount) } : g));
  }, []);

  const recordDamage = useCallback((amount: number) => {
    setGame((g) =>
      g
        ? {
            ...g,
            damage_dealt_total: g.damage_dealt_total + amount,
            cards_played: g.cards_played + 1,
          }
        : g,
    );
  }, []);

  const recordHelp = useCallback(() => {
    setGame((g) => (g ? { ...g, help_requests: g.help_requests + 1 } : g));
  }, []);

  const spawnNextFloor = useCallback(
    (floor: number, enemyHp: number, enemyMaxHp: number, enemyNextDamage: number) => {
      setGame((g) =>
        g
          ? { ...g, floor, enemy_hp: enemyHp, enemy_max_hp: enemyMaxHp, enemy_next_damage: enemyNextDamage }
          : g,
      );
    },
    [],
  );

  const reset = useCallback(() => setGame(null), []);

  return (
    <GameContext.Provider
      value={{
        game,
        initGame,
        setHand,
        unlockCard,
        setPlayerHp,
        setEnemyHp,
        removeCard,
        addShield,
        spendEnergy,
        recordDamage,
        recordHelp,
        spawnNextFloor,
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
