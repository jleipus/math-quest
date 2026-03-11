"use client";

import { useEffect, useState } from "react";
import type React from "react";
import { fetchUserModel, resetUserModel } from "../lib/api";
import { ensureSignedIn } from "../lib/firebase";
import type { TopicRecord, DifficultyRecord } from "../lib/types";
import { difficultyColor, fractionColor } from "../lib/theme";

type Props = {
  showReset?: boolean;
  actions?: React.ReactNode;
};

export default function UserProfile({ showReset = false, actions }: Props) {
  const [topics, setTopics] = useState<TopicRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resetting, setResetting] = useState(false);

  useEffect(() => {
    ensureSignedIn()
      .then(() => fetchUserModel())
      .then((data) => setTopics(data.topics))
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load."))
      .finally(() => setLoading(false));
  }, []);

  async function handleReset() {
    if (!confirm("Reset your progress? This cannot be undone.")) return;
    setResetting(true);
    setError(null);
    try {
      await resetUserModel();
      setTopics([]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Reset failed.");
    } finally {
      setResetting(false);
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <span
          className="font-pixel"
          style={{ fontSize: "0.85rem", color: "var(--px-gold)", letterSpacing: "0.08em" }}
        >
          STUDENT PROFILE
        </span>
        <div className="flex gap-2">
          {showReset && (
            <button
              onClick={handleReset}
              disabled={resetting}
              className="font-pixel"
              style={{
                fontSize: "0.75rem",
                background: "rgba(120,20,20,0.5)",
                border: "2px solid #6a2020",
                color: "#e08080",
                padding: "6px 14px",
                opacity: resetting ? 0.5 : 1,
                cursor: resetting ? "not-allowed" : "pointer",
              }}
            >
              {resetting ? "…" : "Reset"}
            </button>
          )}
          {actions}
        </div>
      </div>

      {/* Body */}
      {loading && (
        <p className="font-pixel" style={{ fontSize: "0.75rem", color: "var(--px-text-dim)" }}>
          Loading…
        </p>
      )}

      {error && (
        <p className="font-pixel" style={{ fontSize: "0.75rem", color: "#e05050" }}>
          {error}
        </p>
      )}

      {!loading && !error && topics.length === 0 && (
        <p className="font-pixel" style={{ fontSize: "0.75rem", color: "var(--px-text-dim)" }}>
          No data yet - answer some tasks first.
        </p>
      )}

      {!loading && !error && topics.length > 0 && (
        <div className="flex flex-col gap-4">
          {/* Column headers */}
          <div
            className="font-pixel grid"
            style={{
              gridTemplateColumns: "1fr 100px 100px 100px",
              fontSize: "0.65rem",
              color: "var(--px-text-dim)",
              paddingBottom: "8px",
              borderBottom: "1px solid var(--px-panel-border)",
              letterSpacing: "0.06em",
            }}
          >
            <span>TOPIC</span>
            <span className="text-center">TRIES</span>
            <span className="text-center">CORRECT</span>
            <span className="text-center">HINTS</span>
          </div>

          {topics.map((rec) => {
            const diffRecords = Object.values(rec.records);
            const totalAttempts = diffRecords.reduce((s, r) => s + r.attempts, 0);
            const totalCorrect = diffRecords.reduce((s, r) => s + r.correct, 0);
            const totalHints = diffRecords.reduce((s, r) => s + r.hints, 0);
            const accuracy = totalAttempts > 0 ? totalCorrect / totalAttempts : 0;
            const barColor = fractionColor(accuracy);

            const orderedDiffs = ["easy", "medium", "hard"]
              .map((d) => rec.records[d])
              .filter((r): r is DifficultyRecord => !!r && r.attempts > 0);

            return (
              <div key={rec.topic}>
                {/* Topic row */}
                <div
                  className="font-pixel grid items-center"
                  style={{
                    gridTemplateColumns: "1fr 100px 100px 100px",
                    fontSize: "0.75rem",
                    color: "var(--px-text)",
                    marginBottom: "6px",
                  }}
                >
                  <span style={{ color: "var(--px-gold)" }}>{rec.topic}</span>
                  <span className="text-center" style={{ color: "var(--px-text-dim)" }}>
                    {totalAttempts}
                  </span>
                  <span className="text-center" style={{ color: difficultyColor.easy }}>
                    {totalCorrect}
                  </span>
                  <span className="text-center" style={{ color: "#a080c0" }}>
                    {totalHints}
                  </span>
                </div>

                {/* Accuracy bar */}
                <div
                  style={{
                    height: 5,
                    background: "#2a0d26",
                    border: "1px solid var(--px-panel-border)",
                    marginBottom: orderedDiffs.length > 0 ? "6px" : "0",
                  }}
                >
                  {totalAttempts > 0 && (
                    <div
                      style={{
                        height: "100%",
                        width: `${accuracy * 100}%`,
                        background: barColor,
                        transition: "width 0.4s",
                      }}
                    />
                  )}
                </div>

                {/* Per-difficulty breakdown */}
                {orderedDiffs.length > 0 && (
                  <div className="flex gap-4 mb-1" style={{ paddingLeft: "8px" }}>
                    {orderedDiffs.map((r) => (
                      <span
                        key={r.difficulty}
                        className="font-pixel"
                        style={{
                          fontSize: "0.6rem",
                          color:
                            difficultyColor[r.difficulty as keyof typeof difficultyColor] ??
                            "var(--px-text-dim)",
                        }}
                      >
                        {r.difficulty.toUpperCase()} {r.correct}/{r.attempts}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
