"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useGame } from "../lib/gameContext";
import { playCard, endTurn } from "../lib/api";
import type { Card } from "../lib/types";
import CardHand from "./CardHand";
import EnemyDisplay from "./EnemyDisplay";
import PlayerHPBar from "./PlayerHPBar";
import TaskModal, { type CardModalState } from "./TaskModal";
import UserModelModal from "./UserModelModal";

type FloatingNumber = {
  id: number;
  value: number;
  x: number;
  color: string;
  prefix: string;
};

export default function BattleScreen() {
  const router = useRouter();
  const {
    game,
    hydrated,
    setEnemyHp,
    setPlayerHp,
    setHand,
    removeCard,
    addShield,
    spendEnergy,
    recordDamage,
    advanceFloor,
  } = useGame();

  const [selectedCard, setSelectedCard] = useState<Card | null>(null);
  const [cardStates, setCardStates] = useState<Map<string, CardModalState>>(new Map());
  const [showUserModel, setShowUserModel] = useState(false);
  const [playingCardId, setPlayingCardId] = useState<string | null>(null);
  const [enemyShake, setEnemyShake] = useState(false);
  const [playerFlash, setPlayerFlash] = useState(false);
  const [floatingNums, setFloatingNums] = useState<FloatingNumber[]>([]);
  const [floatCounter, setFloatCounter] = useState(0);
  const [endingTurn, setEndingTurn] = useState(false);
  const [turnMessage, setTurnMessage] = useState<string | null>(null);
  const [turnMessageKey, setTurnMessageKey] = useState(0);
  const [gameover, setGameover] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (gameover) router.push("/game/gameover");
  }, [gameover, router]);

  useEffect(() => {
    if (hydrated && !game) router.push("/");
  }, [hydrated, game, router]);

  useEffect(() => {
    if (game && game.player_hp <= 0) setGameover(true);
  }, [game?.player_hp]);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (selectedCard) return;
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      if (e.code === "Space") {
        e.preventDefault();
        if (!endingTurn) handleEndTurn();
        return;
      }

      // Num keys: open task modal
      const digit = parseInt(e.key, 10);
      if (!isNaN(digit) && digit >= 1 && digit <= 9 && game) {
        const card = game.hand[digit - 1];
        if (card && game.energy >= card.energy_cost) {
          e.preventDefault();
          setSelectedCard(card);
        }
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [selectedCard, endingTurn, game?.hand, game?.energy]);

  if (!game) return null;

  function addFloatingNumber(value: number, color: string, prefix: string) {
    const id = floatCounter;
    setFloatCounter((n) => n + 1);
    setFloatingNums((prev) => [...prev, { id, value, x: 38 + Math.random() * 24, color, prefix }]);
    setTimeout(() => setFloatingNums((prev) => prev.filter((f) => f.id !== id)), 2000);
  }

  async function handlePlayCard(card: Card) {
    if (!game) return;

    if (game.energy < card.energy_cost) {
      setError(
        `Not enough energy! This card costs ${card.energy_cost} energy (you have ${game.energy}).`,
      );
      return;
    }

    setError(null);
    setPlayingCardId(card.card_id);
    try {
      const result = await playCard({ session_id: game.session_id, card_id: card.card_id });
      spendEnergy(card.energy_cost);

      switch (result.card_type) {
        case "attack":
          setEnemyHp(result.enemy_hp);
          recordDamage(result.effect_value);
          addFloatingNumber(result.effect_value, "#e05050", "-");
          setEnemyShake(true);
          setTimeout(() => setEnemyShake(false), 500);
          break;
        case "heal":
          setPlayerHp(result.player_hp);
          addFloatingNumber(result.effect_value, "#4caf50", "+");
          recordDamage(0);
          break;
        case "shield":
          addShield(result.effect_value);
          addFloatingNumber(result.effect_value, "#6080d0", "🛡");
          recordDamage(0);
          break;
      }

      removeCard(card.card_id);
      setCardStates((prev) => {
        const m = new Map(prev);
        m.delete(card.card_id);
        return m;
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to play card.");
    } finally {
      setPlayingCardId(null);
    }
  }

  async function handleEndTurn() {
    if (!game) return;

    setEndingTurn(true);
    setError(null);
    setTurnMessage(null);
    try {
      const result = await endTurn({ session_id: game.session_id });

      const newEnemy = result.enemy_max_hp !== game.enemy_max_hp;
      if (newEnemy) {
        advanceFloor(result.enemy_hp, result.enemy_max_hp);
        setTurnMessage("Enemy defeated! A new enemy appears.");
      } else {
        setEnemyHp(result.enemy_hp, result.enemy_max_hp);
        setPlayerHp(result.player_hp);
        setPlayerFlash(true);
        setTimeout(() => setPlayerFlash(false), 600);

        const absorbed = result.shield_absorbed;
        const raw = result.enemy_damage;
        const actual = raw - absorbed;
        setTurnMessage(
          absorbed > 0
            ? `Enemy dealt ${raw} dmg — shield absorbed ${absorbed}! You took ${actual}.`
            : `Enemy dealt ${actual} damage!`,
        );
      }
      setTurnMessageKey((k) => k + 1);
      setTimeout(() => setTurnMessage(null), 4000);

      setHand(result.hand, result.enemy_next_damage);
      setCardStates(new Map());
      if (result.player_hp <= 0) setGameover(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to end turn.");
    } finally {
      setEndingTurn(false);
    }
  }

  const energyPips = Array.from({ length: game.max_energy }, (_, i) => i < game.energy);

  return (
    <div
      className="relative flex min-h-screen flex-col p-4 select-none"
      style={{ color: "var(--px-text)" }}
    >
      {/* Top bar */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex flex-col gap-2">
          <PlayerHPBar hp={game.player_hp} maxHp={game.player_max_hp} flash={playerFlash} />

          {game.shield > 0 && (
            <div
              className="font-pixel flex items-center gap-2"
              style={{
                background: "rgba(20,30,100,0.85)",
                border: "3px solid #6080d0",
                boxShadow: "3px 3px 0 #0a0008",
                padding: "8px 14px",
                color: "#a0c0ff",
                fontSize: "1rem",
              }}
            >
              🛡 <span style={{ fontSize: "1.2rem" }}>{game.shield}</span>
              <span style={{ fontSize: "0.6rem", color: "#6080d0" }}>SHIELD</span>
            </div>
          )}
        </div>

        <div className="flex flex-col items-end gap-2">
          <div
            className="font-pixel text-right text-sm"
            style={{
              background: "var(--px-panel)",
              border: "2px solid var(--px-panel-border)",
              boxShadow: "3px 3px 0 #1d0a1a",
              padding: "10px 16px",
              color: "var(--px-text-dim)",
              lineHeight: 1.8,
            }}
          >
            <div style={{ color: "var(--px-text)" }}>{game.grade}</div>
            <div>Floor {game.floor}</div>
          </div>
          <button
            onClick={() => setShowUserModel(true)}
            className="font-pixel"
            style={{
              fontSize: "0.75rem",
              background: "var(--px-panel)",
              border: "2px solid var(--px-panel-border)",
              boxShadow: "3px 3px 0 #1d0a1a",
              color: "var(--px-gold)",
              padding: "6px 12px",
              letterSpacing: "0.06em",
              cursor: "pointer",
            }}
          >
            ⚙️ Profile
          </button>
        </div>
      </div>

      {/* Enemy area */}
      <div className="relative flex flex-1 items-center justify-center">
        <EnemyDisplay
          hp={game.enemy_hp}
          maxHp={game.enemy_max_hp}
          shake={enemyShake}
          nextDamage={game.enemy_next_damage}
        />

        {floatingNums.map((f) => (
          <div
            key={f.id}
            className="pointer-events-none absolute animate-float-up font-pixel text-xl"
            style={{ left: `${f.x}%`, top: "30%", color: f.color, textShadow: "2px 2px 0 #1d0a1a" }}
          >
            {f.prefix}
            {f.value}
          </div>
        ))}

        {turnMessage && (
          <div
            key={turnMessageKey}
            className="pointer-events-none absolute animate-fade-out-up font-pixel text-sm"
            style={{
              bottom: "4%",
              left: 0,
              right: 0,
              marginLeft: "auto",
              marginRight: "auto",
              width: "fit-content",
              whiteSpace: "nowrap",
              background: "rgba(80,40,0,0.88)",
              border: "2px solid var(--px-gold-dim)",
              boxShadow: "3px 3px 0 #0a0008",
              color: "var(--px-gold)",
              padding: "10px 20px",
              lineHeight: 1.8,
            }}
          >
            {turnMessage}
          </div>
        )}
      </div>

      {error && (
        <div
          className="font-pixel mb-3 p-4 text-sm"
          style={{
            background: "rgba(120,20,20,0.6)",
            border: "2px solid #e05050",
            color: "#f8a0a0",
            lineHeight: 1.8,
          }}
        >
          {error}
        </div>
      )}

      {/* End turn + energy row */}
      <div className="mb-3 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="font-pixel text-sm" style={{ color: "var(--px-text-dim)" }}>
            ENERGY
          </span>
          <div className="flex gap-2">
            {energyPips.map((filled, i) => (
              <div
                key={i}
                style={{
                  width: 20,
                  height: 20,
                  background: filled ? "#f5c842" : "#2a0d26",
                  border: `2px solid ${filled ? "#c89e2a" : "#4a2040"}`,
                  boxShadow: filled ? "0 0 6px rgba(245,200,66,0.6)" : "none",
                }}
              />
            ))}
          </div>
          <span className="font-pixel text-sm" style={{ color: "var(--px-gold)" }}>
            {game.energy}/{game.max_energy}
          </span>
        </div>

        <button onClick={handleEndTurn} disabled={endingTurn} className="px-btn px-6 py-3 text-sm">
          {endingTurn ? "…" : "End Turn ↩"}
        </button>
      </div>

      {/* Hand area */}
      <div
        style={{
          background: "var(--px-panel)",
          border: "2px solid var(--px-panel-border)",
          boxShadow: "4px 4px 0 #1d0a1a",
          padding: "16px",
        }}
      >
        <CardHand
          hand={game.hand}
          onClickCard={(card) => setSelectedCard(card)}
          playingCardId={playingCardId}
          energy={game.energy}
        />
      </div>

      {selectedCard && (
        <TaskModal
          card={selectedCard}
          savedState={cardStates.get(selectedCard.card_id)}
          onPlayCard={handlePlayCard}
          onClose={(state) => {
            setCardStates((prev) => new Map(prev).set(selectedCard.card_id, state));
            setSelectedCard(null);
          }}
        />
      )}

      {showUserModel && game && (
        <UserModelModal sessionId={game.session_id} onClose={() => setShowUserModel(false)} />
      )}
    </div>
  );
}
