"use client";

import { useRef, useState, useEffect } from "react";
import type { Card, Stroke } from "../lib/types";
import { recordAnswer, requestHint } from "../lib/api";
import { checkAnswer, penalisedPower } from "../lib/gameLogic";
import { useGame } from "../lib/gameContext";
import HintDisplay from "./HintDisplay";
import DrawingCanvas, { type DrawingCanvasHandle } from "./DrawingCanvas";

/** Persisted state so that closing card modal preserves canvas and message history. */
export type CardModalState = {
  answer: string;
  messages: string[];
  solved: boolean;
  strokes: Stroke[];
  wrongAttempts: number;
};

type Props = {
  card: Card;
  savedState?: CardModalState;
  onPlayCard: (card: Card, effectivePower: number) => void;
  onClose: (state: CardModalState) => void;
};

/** Used for feedback pop-up when answer is submitted. */
type feedbackProps = {
  type: "error" | "success";
  text: string;
};

// TODO: should be global info
const cardTypeInfo: Record<string, { label: string; color: string }> = {
  attack: { label: "Attack", color: "#e05050" },
  heal: { label: "Hela", color: "#4caf50" },
  shield: { label: "Sköld", color: "#6080d0" },
};

export default function CardModal({ card, savedState, onPlayCard, onClose }: Props) {
  const { game, recordWrongAttempt } = useGame();
  const canvasRef = useRef<DrawingCanvasHandle>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Answer player has entered into input box.
  const [answer, setAnswer] = useState(savedState?.answer ?? "");
  // Whether answer submission is being processed.
  const [submitting, setSubmitting] = useState(false);
  // Whether hint request is being processed.
  const [hintLoading, setHintLoading] = useState(false);
  // Hint messages that have been received.
  const [messages, setMessages] = useState<string[]>(savedState?.messages ?? []);
  // Current feedback pop-up.
  const [feedback, setFeedback] = useState<feedbackProps | null>(null);
  // Whether task has been solved.
  const [solved, setSolved] = useState(savedState?.solved ?? false);
  // Incorrect answer attempts.
  const [wrongAttempts, setWrongAttempts] = useState(savedState?.wrongAttempts ?? 0);

  const currentPower = penalisedPower(card.card_power, wrongAttempts);

  function collectState(): CardModalState {
    return {
      answer,
      messages,
      solved,
      strokes: canvasRef.current?.getStrokes() ?? [],
      wrongAttempts: wrongAttempts,
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
  }, [solved, answer, messages, wrongAttempts]);

  async function handleSubmitAnswer() {
    if (!game || !answer.trim() || solved || submitting) return;

    setSubmitting(true);
    setFeedback(null);

    const correct = checkAnswer(answer.trim(), card.task.expected_answer);

    if (correct) {
      setSolved(true);
      setFeedback({ type: "success", text: "Rätt!" });
    } else {
      const newWrongAttempts = wrongAttempts + 1;
      const newPower = penalisedPower(card.card_power, newWrongAttempts);
      const penalty = card.card_power - newPower;
      const penaltyText = penalty > 0 ? ` (-${penalty} power)` : "";

      recordWrongAttempt(card.card_id);
      setWrongAttempts(newWrongAttempts);
      setFeedback({ type: "error", text: `Inte riktigt - försök igen.${penaltyText}` });
    }

    await recordAnswer({
      topic: card.task.topic,
      difficulty: card.task.difficulty,
      correct,
    }).catch(() => {
      // Silently ignore
    });

    setSubmitting(false);
  }

  async function handleRequestHint() {
    if (!game || !canvasRef.current) return;

    setHintLoading(true);

    try {
      const { width, height } = canvasRef.current.getSize();
      const result = await requestHint({
        grade: card.task.grade,
        topic: card.task.topic,
        difficulty: card.task.difficulty,
        question: card.task.question,
        student_work: canvasRef.current.getStrokes(),
        canvas_width: width,
        canvas_height: height,
        previous_hints: messages.length > 0 ? messages : undefined,
      });
      setMessages((prev) => [...prev, result.guiding_question]);
    } catch (e) {
      setFeedback({
        type: "error",
        text: e instanceof Error ? e.message : "Hjälpbegäran misslyckades.",
      });
    } finally {
      setHintLoading(false);
    }
  }

  const typeInfo = cardTypeInfo[card.card_type] ?? cardTypeInfo.attack;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(10,0,8,0.85)", backdropFilter: "blur(4px)" }}
      // Clicking on background closes modal.
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
              UPPGIFT - {card.task.topic.toUpperCase()} ({card.task.difficulty.toUpperCase()})
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
              {solved ? "> Spela kort" : "X"}
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
                if (e.key === "Enter") handleSubmitAnswer();
              }}
              placeholder="Ditt svar..."
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
                onClick={handleSubmitAnswer}
                disabled={submitting || !answer.trim()}
                className="px-btn px-8 py-4 text-base"
              >
                {submitting ? "..." : "Skicka"}
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
              ✏️ Räkna ut det här
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
              onClick={handleRequestHint}
              disabled={hintLoading || solved}
              className="font-pixel w-full text-sm"
              style={{
                background: "rgba(60,30,60,0.7)",
                border: "2px solid var(--px-panel-border)",
                color: "var(--px-pink)",
                padding: "14px 16px",
                cursor: hintLoading || solved ? "not-allowed" : "pointer",
                opacity: hintLoading || solved ? 0.4 : 1,
                boxShadow: "3px 3px 0 #0a0008",
                flexShrink: 0,
              }}
            >
              🤔 Be om en ledtråd
            </button>

            <HintDisplay messages={messages} loading={hintLoading} />
          </div>
        </div>
      </div>
    </div>
  );
}
