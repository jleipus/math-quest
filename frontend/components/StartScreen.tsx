"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { fetchGrades, startSession, fetchHand } from "../lib/api";
import { useGame } from "../lib/gameContext";

export default function StartScreen() {
  const router = useRouter();
  const { initGame: initGameCtx, setHand } = useGame();

  const [grades, setGrades] = useState<string[]>([]);
  const [grade, setGrade] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchGrades()
      .then((g) => {
        setGrades(g);
        setGrade(g[0] ?? "");
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : "Failed to load grades.");
      });
  }, []);

  async function handleStart() {
    if (!grade) return;

    setLoading(true);
    setError(null);
    try {
      const session = await startSession({ grade });
      initGameCtx(session, grade, session.player_hp);

      const drawResp = await fetchHand({
        session_id: session.session_id,
        grade,
      });
      setHand(drawResp.hand);

      router.push("/game");
    } catch {
      setError("Could not connect to the server. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-8">
      {/* Title */}
      <div className="mb-10 text-center">
        <Image src="/logo.png" alt="MathQuest" width={120} height={120} className="mb-4 mx-auto" />
        <h1
          className="font-pixel text-4xl md:text-5xl leading-tight"
          style={{ color: "var(--px-gold)", textShadow: "3px 3px 0 #7a3d00, 6px 6px 0 #1d0a1a" }}
        >
          MathQuest
        </h1>
        <p
          className="mt-5 font-pixel text-sm"
          style={{
            color: "var(--px-text)",
            lineHeight: 2,
            textShadow: "2px 2px 0 #1d0a1a, 4px 4px 0 #0a0008",
          }}
        >
          An AI-guided math learning experience
        </p>
      </div>

      {/* Panel */}
      <div className="px-panel w-full max-w-md rounded-none p-8">
        {/* Topic label */}
        <label className="mb-5 block">
          <span
            className="font-pixel mb-3 block text-sm"
            style={{ color: "var(--px-text-dim)", letterSpacing: "0.08em" }}
          >
            ▶ Select Grade
          </span>
          <select
            value={grade}
            onChange={(e) => setGrade(e.target.value)}
            className="font-pixel w-full px-4 py-3 text-sm"
            style={{
              background: "#1d0a1a",
              border: "2px solid var(--px-panel-border)",
              color: "var(--px-text)",
              outline: "none",
              boxShadow: "inset 0 0 0 1px #0a0008",
            }}
          >
            {grades.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>
        </label>

        {/* Info */}
        <p
          className="font-pixel mb-6 text-sm"
          style={{ color: "var(--px-text)", lineHeight: 2, textShadow: "1px 1px 0 #0a0008" }}
        >
          Each hand has mixed easy, medium &amp; hard tasks. Cards can attack, heal, or shield!
        </p>

        {/* Error */}
        {error && (
          <p
            className="font-pixel mb-4 p-4 text-sm"
            style={{
              background: "rgba(120,20,20,0.6)",
              border: "2px solid #e05050",
              color: "#f8a0a0",
            }}
          >
            {error}
          </p>
        )}

        {/* Start */}
        <button
          onClick={handleStart}
          disabled={loading || !grade}
          className="px-btn w-full py-4 text-sm"
        >
          {loading ? "Loading…" : "▶  Start Game"}
        </button>
      </div>
    </div>
  );
}
