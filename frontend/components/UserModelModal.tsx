"use client";

import { useEffect, useState } from "react";
import { fetchUserModel } from "../lib/api";
import type { TopicRecord, DifficultyRecord } from "../lib/types";

type Props = {
  sessionId: string;
  onClose: () => void;
};

export default function UserModelModal({ sessionId, onClose }: Props) {
  const [topics, setTopics] = useState<TopicRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchUserModel(sessionId)
      .then((data) => setTopics(data.topics))
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load."))
      .finally(() => setLoading(false));
  }, [sessionId]);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(10,0,8,0.85)", backdropFilter: "blur(4px)" }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 780,
          background: "#1d0a1a",
          border: "3px solid var(--px-panel-border)",
          boxShadow: "8px 8px 0 #0a0008",
          padding: "32px 32px 28px",
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <span
            className="font-pixel"
            style={{ fontSize: "0.85rem", color: "var(--px-gold)", letterSpacing: "0.08em" }}
          >
            ⚙️ STUDENT PROFILE
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
            }}
          >
            ✕
          </button>
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
              const barColor =
                accuracy >= 0.7 ? "#4caf50" : accuracy >= 0.4 ? "#f5c842" : "#e05050";

              const diffColor: Record<string, string> = {
                easy: "#4caf50",
                medium: "#f5c842",
                hard: "#e05050",
              };
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
                    <span className="text-center" style={{ color: "#4caf50" }}>
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
                            color: diffColor[r.difficulty] ?? "var(--px-text-dim)",
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
    </div>
  );
}
