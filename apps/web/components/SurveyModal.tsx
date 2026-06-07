"use client";

import { useEffect, useState } from "react";
import { ensureSignedIn, submitSurvey, type SurveyAnswers } from "../lib/firebase";

const SURVEY_SCHEMA_VERSION = 2;

const QUESTIONS: { id: number; text: string }[] = [
  { id: 1, text: "Hur bedömer du din matematikförmåga?" },
  { id: 2, text: "Hur svåra tycker du att matematikuppgifterna är?" },
  { id: 3, text: "Hur hjälpsamma är ledtrådarna när du använder dem?" },
  { id: 4, text: "Hur troligt är det att du spelar det här på fritiden?" },
  { id: 5, text: "Hur stressad känner du dig när du spelar?" },
];

const GENDER_OPTIONS = [
  { value: "male", label: "Man" },
  { value: "female", label: "Kvinna" },
  { value: "other", label: "Annat" },
  { value: "prefer_not_to_say", label: "Vill ej uppge" },
];

type Props = {
  onClose: () => void;
  onSubmit?: () => void;
};

export default function SurveyModal({ onClose, onSubmit }: Props) {
  const [answers, setAnswers] = useState<Partial<SurveyAnswers>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  const allAnswered =
    QUESTIONS.every((q) => answers[q.id] !== undefined) &&
    answers["gender"] !== undefined &&
    answers["age"] !== undefined &&
    String(answers["age"]).trim() !== "";

  async function handleSubmit() {
    if (!allAnswered) return;
    setSubmitting(true);
    setError(null);
    try {
      const user = await ensureSignedIn();
      await submitSurvey({
        uid: user.uid,
        schema_version: SURVEY_SCHEMA_VERSION,
        answers: answers as SurveyAnswers,
      });
      setSubmitted(true);
      onSubmit?.();
      setTimeout(onClose, 1800);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Kunde inte skicka. Försök igen.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(10,0,8,0.88)", backdropFilter: "blur(4px)" }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 520,
          background: "#1d0a1a",
          border: "3px solid var(--px-panel-border)",
          boxShadow: "8px 8px 0 #0a0008",
          padding: "28px 28px 24px",
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <span
            className="font-pixel"
            style={{ fontSize: "0.85rem", color: "var(--px-gold)", letterSpacing: "0.08em" }}
          >
            ÅTERKOPPLINGSENKÄT
          </span>
          <button
            onClick={onClose}
            className="font-pixel"
            style={{
              fontSize: "0.75rem",
              background: "#3d1a35",
              border: "2px solid var(--px-panel-border)",
              color: "var(--px-text-dim)",
              padding: "6px 14px",
              cursor: "pointer",
            }}
          >
            ✕
          </button>
        </div>

        {submitted ? (
          <p
            className="font-pixel text-center"
            style={{ fontSize: "0.8rem", color: "#4caf50", padding: "24px 0" }}
          >
            Tack för din återkoppling!
          </p>
        ) : (
          <>
            <p
              className="font-pixel mb-6"
              style={{ fontSize: "0.7rem", color: "var(--px-text-dim)", lineHeight: 1.7 }}
            >
              Betygsätt varje fråga från 1 till 5.
            </p>

            <div className="flex flex-col gap-6">
              {QUESTIONS.map((q) => (
                <div key={q.id}>
                  <p
                    className="font-pixel mb-3"
                    style={{ fontSize: "0.72rem", color: "var(--px-text)", lineHeight: 1.6 }}
                  >
                    {q.text}
                  </p>
                  <div className="flex gap-2 flex-wrap">
                    {([1, 2, 3, 4, 5] as const).map((val) => {
                      const selected = answers[q.id] === val;
                      return (
                        <button
                          key={val}
                          onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: val }))}
                          className="font-pixel"
                          style={{
                            width: 36,
                            height: 36,
                            fontSize: "0.9rem",
                            background: selected ? "var(--px-gold)" : "#2a0d26",
                            border: `2px solid ${selected ? "var(--px-gold)" : "var(--px-panel-border)"}`,
                            color: selected ? "#1d0a1a" : "var(--px-text-dim)",
                            cursor: "pointer",
                            boxShadow: selected ? "2px 2px 0 #0a0008" : "none",
                            transition: "background 0.1s, color 0.1s",
                          }}
                        >
                          {val}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}

              {/* Gender */}
              <div>
                <p
                  className="font-pixel mb-3"
                  style={{ fontSize: "0.72rem", color: "var(--px-text)", lineHeight: 1.6 }}
                >
                  Vilket kön har du?
                </p>
                <div className="flex gap-2 flex-wrap">
                  {GENDER_OPTIONS.map(({ value, label }) => {
                    const selected = answers["gender"] === value;
                    return (
                      <button
                        key={value}
                        onClick={() => setAnswers((prev) => ({ ...prev, gender: value }))}
                        className="font-pixel"
                        style={{
                          fontSize: "0.65rem",
                          padding: "8px 12px",
                          background: selected ? "var(--px-gold)" : "#2a0d26",
                          border: `2px solid ${selected ? "var(--px-gold)" : "var(--px-panel-border)"}`,
                          color: selected ? "#1d0a1a" : "var(--px-text-dim)",
                          cursor: "pointer",
                          boxShadow: selected ? "2px 2px 0 #0a0008" : "none",
                          transition: "background 0.1s, color 0.1s",
                        }}
                      >
                        {label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Age */}
              <div>
                <p
                  className="font-pixel mb-3"
                  style={{ fontSize: "0.72rem", color: "var(--px-text)", lineHeight: 1.6 }}
                >
                  Hur gammal är du?
                </p>
                <input
                  type="number"
                  min={1}
                  max={120}
                  value={answers["age"] !== undefined ? String(answers["age"]) : ""}
                  onChange={(e) => setAnswers((prev) => ({ ...prev, age: e.target.value }))}
                  className="font-pixel"
                  style={{
                    width: 90,
                    padding: "8px 10px",
                    fontSize: "0.8rem",
                    background: "#2a0d26",
                    border: "2px solid var(--px-panel-border)",
                    color: "var(--px-text)",
                    outline: "none",
                  }}
                />
              </div>
            </div>

            {error && (
              <p className="font-pixel mt-4" style={{ fontSize: "0.7rem", color: "#e05050" }}>
                {error}
              </p>
            )}

            <div className="flex items-center justify-between mt-8">
              <span
                className="font-pixel"
                style={{ fontSize: "0.65rem", color: "var(--px-text-dim)" }}
              >
                {QUESTIONS.filter((q) => answers[q.id] !== undefined).length +
                  (answers["gender"] !== undefined ? 1 : 0) +
                  (answers["age"] !== undefined && String(answers["age"]).trim() !== "" ? 1 : 0)}
                /{QUESTIONS.length + 2} besvarade
              </span>
              <button
                onClick={handleSubmit}
                disabled={!allAnswered || submitting}
                className="px-btn font-pixel"
                style={{
                  fontSize: "0.75rem",
                  padding: "10px 24px",
                  opacity: !allAnswered || submitting ? 0.45 : 1,
                  cursor: !allAnswered || submitting ? "not-allowed" : "pointer",
                }}
              >
                {submitting ? "..." : "Skicka"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
