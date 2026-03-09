"use client";

import { useRef, useState, useEffect } from "react";
import type { Card, Stroke } from "../lib/types";
import { recordAnswer, requestHint } from "../lib/api";
import { checkAnswer, penalisedPower } from "../lib/gameLogic";
import { useGame } from "../lib/gameContext";
import AgentChat from "./AgentChat";
import DrawingCanvas, { type DrawingCanvasHandle } from "./DrawingCanvas";

export type CardModalState = {
  answer: string;
  messages: string[];
  solved: boolean;
  strokes: Stroke[];
};

type Props = {
  card: Card;
  savedState?: CardModalState;
  /** Current wrong-attempt count for this card. */
  wrongAttempts: number;
  onPlayCard: (card: Card, effectivePower: number) => void;
  onClose: (state: CardModalState) => void;
};

const cardTypeInfo: Record<string, { label: string; color: string }> = {
  attack: { label: "Attack", color: "#e05050" },
  heal: { label: "Heal", color: "#4caf50" },
  shield: { label: "Shield", color: "#6080d0" },
};

export default function TaskModal({ card, savedState, wrongAttempts, onPlayCard, onClose }: Props) {
  const {
    game,
    recordHelp,
    recordWrongAttempt,
    recordLocalAttempt,
    recordLocalHint,
    localTopicRecords,
  } = useGame();
  const canvasRef = useRef<DrawingCanvasHandle>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const [answer, setAnswer] = useState(savedState?.answer ?? "");
  const [submitting, setSubmitting] = useState(false);
  const [helpLoading, setHelpLoading] = useState(false);
  const [messages, setMessages] = useState<string[]>(savedState?.messages ?? []);
  const [feedback, setFeedback] = useState<{ type: "error" | "success"; text: string } | null>(
    null,
  );
  const [solved, setSolved] = useState(savedState?.solved ?? false);
  const [localWrongAttempts, setLocalWrongAttempts] = useState(wrongAttempts);

  const currentPower = penalisedPower(card.card_power, localWrongAttempts);

  function collectState(): CardModalState {
    return {
      answer,
      messages,
      solved,
      strokes: canvasRef.current?.getStrokes() ?? [],
    };
  }

  function handleClose() {
    if (solved) onPlayCard(card, currentPower);
    onClose(collectState());
  }

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") handleClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [solved, answer, messages, localWrongAttempts]);

  async function handleSubmit() {
    if (!game || !answer.trim() || solved) return;
    setSubmitting(true);
    setFeedback(null);

    const correct = checkAnswer(answer.trim(), card.task.expected_answer);

    if (correct) {
      setSolved(true);
      setFeedback({ type: "success", text: "Correct!" });
    } else {
      const newWrongs = localWrongAttempts + 1;
      setLocalWrongAttempts(newWrongs);
      recordWrongAttempt(card.card_id);
      const newPower = penalisedPower(card.card_power, newWrongs);
      const penalty = card.card_power - newPower;
      const penaltyText = penalty > 0 ? ` (-${penalty} power)` : "";
      setFeedback({ type: "error", text: `Not quite - try again.${penaltyText}` });
    }

    // Update local user model
    recordLocalAttempt(card.task.topic, card.task.difficulty, correct);

    recordAnswer({
      topic: card.task.topic,
      difficulty: card.task.difficulty,
      correct,
    }).catch(() => {
      // Silently ignore
    });

    setSubmitting(false);
  }

  async function handleHelp() {
    if (!game || !canvasRef.current) return;
    setHelpLoading(true);
    recordHelp();
    try {
      const { width, height } = canvasRef.current.getSize();
      // Update local user model for hint
      recordLocalHint(card.task.topic, card.task.difficulty);

      const result = await requestHint({
        grade: card.task.grade,
        topic: card.task.topic,
        difficulty: card.task.difficulty,
        question: card.task.question,
        user_model: localTopicRecords.length > 0 ? localTopicRecords : undefined,
        student_work: canvasRef.current.getStrokes(),
        canvas_width: width,
        canvas_height: height,
        previous_questions: messages.length > 0 ? messages : undefined,
      });
      setMessages((prev) => [...prev, result.guiding_question]);
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
      onClick={(e) => {
        if (e.target === e.currentTarget) handleClose();
      }}
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
        {/* Header */}
        <div className="mb-6">
          <div className="mb-3 flex items-center gap-4">
            <span className="font-pixel text-sm" style={{ color: "var(--px-text-dim)" }}>
              TASK - {card.task.topic.toUpperCase()} ({card.task.difficulty.toUpperCase()})
            </span>
            <span className="font-pixel text-sm" style={{ color: typeInfo.color }}>
              {typeInfo.label} - {currentPower} pts
              {currentPower < card.card_power ? ` (-${card.card_power - currentPower})` : ""}
            </span>
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

        {/* Answer row */}
        <div className="relative mb-6">
          <div className="flex gap-3">
            <input
              ref={inputRef}
              type="text"
              value={answer}
              onChange={(e) => {
                if (!solved) setAnswer(e.target.value);
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSubmit();
              }}
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

          {feedback && (
            <div
              className={`font-pixel text-sm ${feedback.type === "error" ? "animate-shake" : ""}`}
              style={{
                position: "absolute",
                top: "100%",
                left: 0,
                right: 380 + 24,
                marginTop: 6,
                padding: "8px 16px",
                background:
                  feedback.type === "success" ? "rgba(10,40,10,0.97)" : "rgba(60,10,10,0.97)",
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

        {/* Two-column body: canvas | hint + chat */}
        <div className="flex gap-6" style={{ flex: 1, minHeight: 0, alignItems: "stretch" }}>
          <div style={{ flex: "1 1 0", minWidth: 0, display: "flex", flexDirection: "column" }}>
            <p
              className="font-pixel mb-3 text-sm"
              style={{ color: "var(--px-text-dim)", flexShrink: 0 }}
            >
              ✏️ Work it out here
            </p>
            <div style={{ border: "2px solid var(--px-panel-border)", flex: 1, minHeight: 0 }}>
              <DrawingCanvas ref={canvasRef} initialStrokes={savedState?.strokes} />
            </div>
          </div>

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
                cursor: helpLoading || solved ? "not-allowed" : "pointer",
                opacity: helpLoading || solved ? 0.4 : 1,
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
