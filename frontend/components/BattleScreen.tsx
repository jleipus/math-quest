"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useGame } from "../lib/gameContext";
import { playCard, endTurn, nextFloor, drawHand } from "../lib/api";
import { ENERGY_COST } from "../lib/types";
import type { Card } from "../lib/types";
import CardHand from "./CardHand";
import EnemyDisplay from "./EnemyDisplay";
import PlayerHPBar from "./PlayerHPBar";
import TaskModal from "./TaskModal";

type FloatingNumber = { id: number; value: number; x: number; color: string; prefix: string };

export default function BattleScreen() {
  const router = useRouter();
  const {
    game,
    setEnemyHp,
    setPlayerHp,
    setHand,
    removeCard,
    addShield,
    spendEnergy,
    recordDamage,
    spawnNextFloor,
  } = useGame();

  const [selectedCard, setSelectedCard] = useState<Card | null>(null);
  const [playingCardId, setPlayingCardId] = useState<string | null>(null);
  const [enemyShake, setEnemyShake] = useState(false);
  const [playerFlash, setPlayerFlash] = useState(false);
  const [floatingNums, setFloatingNums] = useState<FloatingNumber[]>([]);
  const [floatCounter, setFloatCounter] = useState(0);
  const [endingTurn, setEndingTurn] = useState(false);
  const [turnMessage, setTurnMessage] = useState<string | null>(null);
  const [turnMessageKey, setTurnMessageKey] = useState(0);
  const [outcome, setOutcome] = useState<"victory" | "gameover" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [enemyDefeated, setEnemyDefeated] = useState(false);

  useEffect(() => {
    if (outcome === "victory") router.push("/game/victory");
    if (outcome === "gameover") router.push("/game/gameover");
  }, [outcome, router]);

  useEffect(() => {
    if (!game) router.push("/");
  }, [game, router]);

  useEffect(() => {
    if (game && game.player_hp <= 0) setOutcome("gameover");
  }, [game?.player_hp]);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      // Don't fire when the task modal is open or typing in an input
      if (selectedCard) return;
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      // Space → end turn
      if (e.code === "Space") {
        e.preventDefault();
        if (!endingTurn) handleEndTurn();
        return;
      }

      // 1–9 → open task modal for that card index (if affordable)
      const digit = parseInt(e.key, 10);
      if (!isNaN(digit) && digit >= 1 && digit <= 9 && game) {
        const card = game.hand[digit - 1];
        if (card) {
          const cost = ENERGY_COST[card.task.difficulty];
          if (game.energy >= cost) setSelectedCard(card);
        }
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCard, endingTurn, game?.hand, game?.energy]);

  if (!game) return null;

  function addFloatingNumber(value: number, color: string, prefix: string) {
    const id = floatCounter;
    setFloatCounter((n) => n + 1);
    setFloatingNums((prev) => [
      ...prev,
      { id, value, x: 38 + Math.random() * 24, color, prefix },
    ]);
    setTimeout(() => setFloatingNums((prev) => prev.filter((f) => f.id !== id)), 1200);
  }

  async function handlePlayCard(card: Card) {
    if (!game) return;
    const cost = ENERGY_COST[card.task.difficulty];
    if (game.energy < cost) {
      setError(`Not enough energy! This card costs ${cost} energy (you have ${game.energy}).`);
      return;
    }
    setError(null);
    setPlayingCardId(card.card_id);
    try {
      const result = await playCard({ session_id: game.session_id, card_id: card.card_id });
      spendEnergy(cost);

      if (result.card_type === "attack") {
        setEnemyHp(result.enemy_hp);
        recordDamage(result.effect_value);
        addFloatingNumber(result.effect_value, "#e05050", "-");
        setEnemyShake(true);
        setTimeout(() => setEnemyShake(false), 500);
        if (result.enemy_defeated) {
          setEnemyDefeated(true);
          // Don't spawn new enemy yet — wait for player to end their turn
        }
      } else if (result.card_type === "heal") {
        setPlayerHp(result.player_hp);
        addFloatingNumber(result.effect_value, "#4caf50", "+");
        recordDamage(0);
      } else if (result.card_type === "shield") {
        addShield(result.effect_value);
        addFloatingNumber(result.effect_value, "#6080d0", "🛡");
        recordDamage(0);
      }

      removeCard(card.card_id);
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
      if (enemyDefeated) {
        // Enemy already dead — advance floor then just draw cards (no enemy attack)
        const floorResp = await nextFloor({ session_id: game.session_id });
        spawnNextFloor(floorResp.floor, floorResp.enemy_hp, floorResp.enemy_max_hp, floorResp.enemy_next_damage);
        setEnemyDefeated(false);
        const drawResp = await drawHand({ session_id: game.session_id });
        setHand(drawResp.hand, floorResp.enemy_next_damage);
        setTurnMessage(`Floor ${floorResp.floor}! A new enemy appears!`);
        setTurnMessageKey((k) => k + 1);
        setTimeout(() => setTurnMessage(null), 4000);
      } else {
        const result = await endTurn({ session_id: game.session_id });
        setPlayerHp(result.player_hp);
        setPlayerFlash(true);
        setTimeout(() => setPlayerFlash(false), 600);

        const absorbed = result.shield_absorbed;
        const raw = result.enemy_damage;
        const actual = raw - absorbed;
        const msg =
          absorbed > 0
            ? `Enemy dealt ${raw} dmg — shield absorbed ${absorbed}! You took ${actual}.`
            : `Enemy dealt ${actual} damage!`;
        setTurnMessage(msg);
        setTurnMessageKey((k) => k + 1);
        setTimeout(() => setTurnMessage(null), 4000);

        setHand(result.hand, result.enemy_next_damage);
        if (result.player_hp <= 0) setOutcome("gameover");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to end turn.");
    } finally {
      setEndingTurn(false);
    }
  }

  // Energy pips
  const energyPips = Array.from({ length: game.max_energy }, (_, i) => i < game.energy);

  return (
    <div
      className="relative flex min-h-screen flex-col p-4 select-none"
      style={{ color: "var(--px-text)" }}
    >
      {/* Top bar */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex flex-col gap-2">
          <PlayerHPBar
            hp={game.player_hp}
            maxHp={game.player_max_hp}
            flash={playerFlash}
          />
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
          <div style={{ color: "var(--px-text)" }}>{game.topic}</div>
          <div>Floor {game.floor}</div>
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

        {/* Floating numbers */}
        {floatingNums.map((f) => (
          <div
            key={f.id}
            className="pointer-events-none absolute animate-float-up font-pixel text-xl"
            style={{ left: `${f.x}%`, top: "30%", color: f.color, textShadow: "2px 2px 0 #1d0a1a" }}
          >
            {f.prefix}{f.value}
          </div>
        ))}

        {/* Turn message — floats over enemy area, auto-fades, fits content width */}
        {turnMessage && (
          <div
            key={turnMessageKey}
            className="pointer-events-none absolute animate-fade-out-up font-pixel text-sm"
            style={{
              bottom: "4%",
              left: "50%",
              transform: "translateX(-50%)",
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

      {/* Error */}
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
        {/* Energy display */}
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

        <button
          onClick={handleEndTurn}
          disabled={endingTurn}
          className="px-btn px-6 py-3 text-sm"
        >
          {endingTurn ? "…" : enemyDefeated ? "Next Floor ▶" : "End Turn ↩"}
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
          onPlayCard={handlePlayCard}
          playingCardId={playingCardId}
          energy={game.energy}
        />
      </div>

      {/* Task modal — passes handlePlayCard so it auto-plays on correct answer */}
      {selectedCard && (
        <TaskModal
          card={selectedCard}
          onPlayCard={handlePlayCard}
          onClose={() => setSelectedCard(null)}
        />
      )}
    </div>
  );
}
