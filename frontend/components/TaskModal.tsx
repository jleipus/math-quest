"use client";

import { useRef, useState, useEffect } from "react";
import type { AgentMessage, Card } from "../lib/types";
import { requestHelp, submitAnswer } from "../lib/api";
import { useGame } from "../lib/gameContext";
import AgentChat from "./AgentChat";
import DrawingCanvas, { type DrawingCanvasHandle } from "./DrawingCanvas";

type Props = {
  card: Card;
  onPlayCard: (card: Card) => void;
  onClose: () => void;
};

const cardTypeInfo: Record<string, { icon: string; label: string; color: string }> = {
  attack: { icon: "⚔️", label: "Attack", color: "#e05050" },
  heal:   { icon: "💚", label: "Heal",   color: "#4caf50" },
  shield: { icon: "🛡️", label: "Shield", color: "#6080d0" },
};

export default function TaskModal({ card, onPlayCard, onClose }: Props) {
  const { game, unlockCard } = useGame();
  const canvasRef = useRef<DrawingCanvasHandle>(null);
  const [answer, setAnswer] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [helpLoading, setHelpLoading] = useState(false);
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [feedback, setFeedback] = useState<{ type: "error" | "success"; text: string } | null>(null);
  const [solved, setSolved] = useState(false);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") handleClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  // handleClose is stable (no deps change) — listing solved keeps it correct
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [solved]);

  async function handleSubmit() {
    if (!game || !answer.trim() || solved) return;
    setSubmitting(true);
    setFeedback(null);
    try {
      const result = await submitAnswer({
        session_id: game.session_id,
        task_id: card.task.task_id,
        answer: answer.trim(),
      });
      if (result.correct) {
        unlockCard(card.card_id);
        setSolved(true);
        setFeedback({ type: "success", text: result.message });
      } else {
        setFeedback({ type: "error", text: result.message });
      }
    } catch {
      setFeedback({ type: "error", text: "Something went wrong. Try again." });
    } finally {
      setSubmitting(false);
    }
  }

  function handleClose() {
    if (solved) {
      onPlayCard({ ...card, locked: false });
    }
    onClose();
  }

  async function handleHelp() {
    if (!game || !canvasRef.current) return;
    setHelpLoading(true);
    try {
      const result = await requestHelp({
        session_id: game.session_id,
        task_id: card.task.task_id,
        student_work: canvasRef.current.getStrokes(),
      });
      setMessages((prev) => [...prev, { guiding_question: result.guiding_question }]);
    } catch (e) {
      setFeedback({ type: "error", text: e instanceof Error ? e.message : "Help request failed." });
    } finally {
      setHelpLoading(false);
    }
  }

  const typeInfo = cardTypeInfo[card.card_type] ?? cardTypeInfo.attack;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(10,0,8,0.85)", backdropFilter: "blur(4px)" }}
      onClick={(e) => { if (e.target === e.currentTarget) handleClose(); }}
    >
      <div
        className="relative w-full flex flex-col"
        style={{
          maxWidth: 1400,
          height: "95vh",
          background: "#1d0a1a",
          border: "3px solid var(--px-panel-border)",
          boxShadow: "8px 8px 0 #0a0008",
          padding: "36px 36px 32px",
        }}
      >
        {/* ── Header: task info + close button in same row (no overlap) ── */}
        <div className="mb-6">
          <div className="mb-3 flex items-center gap-4">
            <span className="font-pixel text-sm" style={{ color: "var(--px-text-dim)" }}>
              TASK — {card.task.topic.toUpperCase()} ({card.task.difficulty.toUpperCase()})
            </span>
            <span className="font-pixel text-sm" style={{ color: typeInfo.color }}>
              {typeInfo.icon} {typeInfo.label} · {card.card_power} pts
            </span>
            {/* Close / Play button — inline so it never covers the text above */}
            <button
              onClick={handleClose}
              className="font-pixel text-sm ml-auto"
              style={{
                flexShrink: 0,
                background: solved ? "#1a3d1a" : "#3d1a35",
                border: `2px solid ${solved ? "#4caf50" : "var(--px-panel-border)"}`,
                color: solved ? "#80e080" : "var(--px-text-dim)",
                padding: "6px 14px",
              }}
              aria-label="Close"
            >
              {solved ? "▶ Play Card" : "✕"}
            </button>
          </div>
          <h2
            className="font-pixel leading-relaxed"
            style={{
              fontSize: "1.6rem",
              color: "var(--px-gold)",
              textShadow: "3px 3px 0 #3a1a00, 5px 5px 0 #0a0008",
            }}
          >
            {card.task.question}
          </h2>
        </div>

        {/* ── Answer row + feedback overlay ── */}
        <div className="relative mb-6">
          <div className="flex gap-3">
            <input
              type="text"
              value={answer}
              onChange={(e) => { if (!solved) setAnswer(e.target.value); }}
              onKeyDown={(e) => { if (e.key === "Enter") handleSubmit(); }}
              placeholder="Your answer…"
              disabled={solved}
              className="font-pixel flex-1 px-5 py-4 text-lg"
              style={{
                background: "#0a0008",
                border: "2px solid var(--px-panel-border)",
                color: "var(--px-text)",
                outline: "none",
                cursor: solved ? "default" : "text",
              }}
            />
            {!solved && (
              <button
                onClick={handleSubmit}
                disabled={submitting || !answer.trim()}
                className="px-btn px-8 py-4 text-base"
              >
                {submitting ? "…" : "Submit"}
              </button>
            )}
          </div>

          {/* Feedback — absolutely positioned below the input, constrained to canvas column width */}
          {feedback && (
            <div
              className={`font-pixel text-sm ${feedback.type === "error" ? "animate-shake" : ""}`}
              style={{
                position: "absolute",
                top: "100%",
                left: 0,
                // Stop before the hint column (380px wide + 24px gap)
                right: 380 + 24,
                marginTop: 6,
                padding: "8px 16px",
                background: feedback.type === "success" ? "rgba(10,40,10,0.97)" : "rgba(60,10,10,0.97)",
                border: `2px solid ${feedback.type === "success" ? "#4caf50" : "#e05050"}`,
                color: feedback.type === "success" ? "#80e080" : "#f8a0a0",
                zIndex: 10,
                boxShadow: "3px 3px 0 #0a0008",
              }}
            >
              {feedback.text}
            </div>
          )}
        </div>

        {/* ── Two-column body: canvas | hint + chat ── */}
        <div className="flex gap-6" style={{ flex: 1, minHeight: 0, alignItems: "stretch" }}>

          {/* Left: drawing canvas */}
          <div style={{ flex: "1 1 0", minWidth: 0, display: "flex", flexDirection: "column" }}>
            <p className="font-pixel mb-3 text-sm" style={{ color: "var(--px-text-dim)", flexShrink: 0 }}>
              ✏️ Work it out here
            </p>
            <div style={{ border: "2px solid var(--px-panel-border)", flex: 1, minHeight: 0 }}>
              <DrawingCanvas ref={canvasRef} />
            </div>
          </div>

          {/* Right: hint button + chat */}
          <div
            style={{
              width: 380,
              flexShrink: 0,
              display: "flex",
              flexDirection: "column",
              gap: 16,
              minHeight: 0,
            }}
          >
            <button
              onClick={handleHelp}
              disabled={helpLoading || solved}
              className="font-pixel w-full text-sm"
              style={{
                background: "rgba(60,30,60,0.7)",
                border: "2px solid var(--px-panel-border)",
                color: "var(--px-pink)",
                padding: "14px 16px",
                cursor: (helpLoading || solved) ? "not-allowed" : "pointer",
                opacity: (helpLoading || solved) ? 0.4 : 1,
                boxShadow: "3px 3px 0 #0a0008",
                flexShrink: 0,
              }}
            >
              🤔 Ask for a hint
            </button>

            <AgentChat messages={messages} loading={helpLoading} />
          </div>
        </div>
      </div>
    </div>
  );
}
