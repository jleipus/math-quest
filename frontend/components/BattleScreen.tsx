"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useGame } from "../lib/gameContext";
import { fetchHand } from "../lib/api";
import { canPlayCard } from "../lib/gameLogic";
import type { Card } from "../lib/types";
import { cardTypeTheme } from "../lib/theme";
import CardHand from "./CardHand";
import EnemyDisplay from "./EnemyDisplay";
import PlayerDisplay from "./PlayerDisplay";
import CardModal, { type CardModalState } from "./CardModal";
import UserModelModal from "./UserModelModal";
import PauseMenu from "./PauseMenu";
import TutorialOverlay from "./TutorialOverlay";
import SurveyModal from "./SurveyModal";

type FloatingNumber = {
  id: number;
  value: number;
  x: number;
  color: string;
};

export default function BattleScreen() {
  const router = useRouter();
  const { game, hydrated, playCard, endTurn, getWrongAttempts, isGameOver } = useGame();

  // TODO: add short comment for each useState and useEffect

  const [selectedCard, setSelectedCard] = useState<Card | null>(null);
  const [cardStates, setCardStates] = useState<Map<string, CardModalState>>(new Map());
  const [showUserModel, setShowUserModel] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
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
  const [showTutorial, setShowTutorial] = useState(false);
  const [showSurvey, setShowSurvey] = useState(false);
  const [surveySubmitted, setSurveySubmitted] = useState(false);

  const tutorialShown = useRef(false);

  useEffect(() => {
    if (gameover) router.push("/game/gameover");
  }, [gameover, router]);

  useEffect(() => {
    if (hydrated && !game) router.push("/");
  }, [hydrated, game, router]);

  useEffect(() => {
    if (game && isGameOver()) setGameover(true);
  }, [game?.playerHP]);

  // Show tutorial once when the first hand arrives (floor 1, turn 1)
  useEffect(() => {
    if (!game?.hand?.length || game.floor !== 1 || game.turn !== 1) return;
    if (tutorialShown.current) return;

    tutorialShown.current = true;
    setShowTutorial(true);
  }, [game?.turn, game?.floor]);

  useEffect(() => {
    if (!game?.hand?.length) return;

    console.groupCollapsed(`[MathQuest] Floor ${game.floor}, Turn ${game.turn}`);
    console.table(
      game.hand.map((card) => ({
        card: card.card_name,
        type: card.card_type,
        difficulty: card.task.difficulty,
        topic: card.task.topic,
        question: card.task.question,
        answer: card.task.expected_answer,
      })),
    );
    console.groupEnd();
  }, [game?.turn]);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (selectedCard || showUserModel || showTutorial) return;
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      // Open/close menu on `Escape`
      if (e.key === "Escape") {
        e.preventDefault();
        setShowMenu((prev) => !prev);
        return;
      }

      // If menu is open, ignore other keypresses
      if (showMenu) return;

      // End turn on `Space`
      if (e.code === "Space") {
        e.preventDefault();
        if (!endingTurn) handleEndTurn();
        return;
      }

      // Open card on number
      const digit = parseInt(e.key, 10);
      if (!isNaN(digit) && digit >= 1 && digit <= 9 && game) {
        const card = game.hand[digit - 1];
        if (card && canPlayCard(game.energy, card) && !endingTurn && game.enemyHP > 0) {
          e.preventDefault();
          setSelectedCard(card);
        }
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [selectedCard, showUserModel, showTutorial, showMenu, endingTurn, game?.hand, game?.energy]);

  if (!game) return null;

  /** Display pop-up info text that dissapears after 2 seconds. */
  function addFloatingNumber(value: number, color: string) {
    const id = floatCounter;
    setFloatCounter((n) => n + 1);
    setFloatingNums((prev) => [...prev, { id, value, x: 38 + Math.random() * 24, color }]);
    setTimeout(() => setFloatingNums((prev) => prev.filter((f) => f.id !== id)), 2000);
  }

  /** Handler called by card modal when task is solved and window is closed. */
  function handlePlayCard(card: Card, effectivePower: number) {
    if (!game) return;

    if (!canPlayCard(game.energy, card)) {
      setError(
        `Not enough energy! This card costs ${card.energy_cost} energy (you have ${game!.energy}).`,
      );
      return;
    }

    setError(null);
    setPlayingCardId(card.card_id);

    playCard(card, effectivePower);

    addFloatingNumber(card.card_power, cardTypeTheme[card.card_type].floatColor);
    if (card.card_type === "attack") {
      setEnemyShake(true);
      setTimeout(() => setEnemyShake(false), 500);
    }

    // Remove card modal state
    setCardStates((prev) => {
      const m = new Map(prev);
      m.delete(card.card_id);
      return m;
    });
    setPlayingCardId(null);
  }

  async function handleEndTurn() {
    if (!game) return;

    setEndingTurn(true);
    setError(null);
    setTurnMessage(null);

    try {
      const handResp = await fetchHand({ grade: game!.grade });

      // Compute damage before state updates (game is a stale closure after endTurn)
      const enemyDefeated = game.enemyHP <= 0;
      const absorbed = Math.min(game.shield, game.enemyDamage);
      const damageTaken = enemyDefeated ? 0 : game.enemyDamage - absorbed;

      endTurn(handResp.hand);

      if (enemyDefeated) {
        setTurnMessage("Enemy defeated! A new enemy appears.");
      } else {
        if (damageTaken > 0) {
          setPlayerFlash(true);
          setTimeout(() => setPlayerFlash(false), 600);
          setTurnMessage(`Enemy dealt ${damageTaken} damage!`);
        } else {
          setTurnMessage(`Shield absorbed all damage.`);
        }
      }

      setTurnMessageKey((k) => k + 1);
      setTimeout(() => setTurnMessage(null), 4000);
      setCardStates(new Map());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to end turn.");
    } finally {
      setEndingTurn(false);
    }
  }

  const energyPips = Array.from({ length: game.maxEnergy }, (_, i) => i < game.energy);

  return (
    <div
      className="relative flex min-h-screen flex-col p-4 select-none"
      style={{ color: "var(--px-text)" }}
    >
      {/* Top bar */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex flex-col gap-2">
          <div data-tutorial="player-hp">
            <PlayerDisplay hp={game.playerHP} maxHp={game.playerMaxHP} flash={playerFlash} />
          </div>

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
              padding: "10px 18px",
              color: "var(--px-text-dim)",
              lineHeight: 1.8,
            }}
          >
            <div style={{ color: "var(--px-text)" }}>{game.grade}</div>
            <div>Floor {game.floor}</div>
            <div>Turn {game.turn}</div>
          </div>
          <div className="flex gap-2">
            <button
              data-tutorial="profile-btn"
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
              Profile
            </button>
            <button
              onClick={() => setShowMenu(true)}
              className="font-pixel"
              style={{
                fontSize: "0.75rem",
                background: "var(--px-panel)",
                border: "2px solid var(--px-panel-border)",
                boxShadow: "3px 3px 0 #1d0a1a",
                color: "var(--px-text-dim)",
                padding: "6px 12px",
                letterSpacing: "0.06em",
                cursor: "pointer",
              }}
            >
              ☰
            </button>
          </div>
        </div>
      </div>

      {/* Enemy area */}
      <div className="relative flex flex-1 items-center justify-center">
        <div data-tutorial="enemy">
          <EnemyDisplay
            hp={game.enemyHP}
            maxHP={game.enemyMaxHP}
            shake={enemyShake}
            nextDamage={game.enemyDamage}
          />
        </div>

        {floatingNums.map((f) => (
          <div
            key={f.id}
            className="pointer-events-none absolute animate-float-up font-pixel text-xl"
            style={{ left: `${f.x}%`, top: "30%", color: f.color, textShadow: "2px 2px 0 #1d0a1a" }}
          >
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

      {/* Feedback row */}
      {!surveySubmitted && (
        <div className="mb-2 flex justify-end">
          <button
            onClick={() => setShowSurvey(true)}
            className="font-pixel"
            style={{
              fontSize: "0.65rem",
              background: "var(--px-panel)",
              border: "2px solid var(--px-panel-border)",
              boxShadow: "3px 3px 0 #1d0a1a",
              color: "var(--px-text-dim)",
              padding: "5px 10px",
              letterSpacing: "0.06em",
              cursor: "pointer",
            }}
          >
            Feedback
          </button>
        </div>
      )}

      {/* Energy + end turn row */}
      <div className="mb-2 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="font-pixel text-m" style={{ color: "var(--px-text-dim)" }}>
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
          <span className="font-pixel text-m" style={{ color: "var(--px-gold)" }}>
            {game.energy}/{game.maxEnergy}
          </span>
        </div>
        <button
          data-tutorial="end-turn"
          onClick={handleEndTurn}
          disabled={endingTurn}
          className="px-btn px-6 py-3 text-sm"
        >
          {endingTurn ? "…" : "End Turn ↩"}
        </button>
      </div>

      {/* Hand area */}
      <div
        data-tutorial="hand"
        style={{
          background: "var(--px-panel)",
          border: "2px solid var(--px-panel-border)",
          boxShadow: "4px 4px 0 #1d0a1a",
          padding: "16px",
        }}
      >
        <CardHand
          hand={game.hand}
          onClickCard={(card) => {
            if (!endingTurn && game.enemyHP > 0) setSelectedCard(card);
          }}
          playingCardId={playingCardId}
          energy={game.enemyHP > 0 ? game.energy : 0}
        />
      </div>

      {selectedCard && (
        <CardModal
          card={selectedCard}
          savedState={cardStates.get(selectedCard.card_id)}
          onPlayCard={handlePlayCard}
          onClose={(state) => {
            setCardStates((prev) => new Map(prev).set(selectedCard.card_id, state));
            setSelectedCard(null);
          }}
        />
      )}

      {showUserModel && <UserModelModal onClose={() => setShowUserModel(false)} />}

      {showMenu && <PauseMenu onResume={() => setShowMenu(false)} />}

      {showSurvey && (
        <SurveyModal
          onClose={() => setShowSurvey(false)}
          onSubmit={() => setSurveySubmitted(true)}
        />
      )}

      {showTutorial && <TutorialOverlay onDone={() => setShowTutorial(false)} />}
    </div>
  );
}
