"use client";

import { fractionColor } from "../lib/theme";

type Props = {
  hp: number;
  maxHp: number;
  flash: boolean;
};

export default function PlayerDisplay({ hp, maxHp, flash }: Props) {
  const pct = Math.max(0, Math.min(100, (hp / maxHp) * 100));
  const barColor = fractionColor(pct / 100);

  return (
    <div
      className={flash ? "animate-damage-flash" : ""}
      style={{
        background: "var(--px-panel)",
        border: "2px solid var(--px-panel-border)",
        boxShadow: "3px 3px 0 #1d0a1a",
        padding: "10px 14px",
        minWidth: 200,
      }}
    >
      {/* Label + numbers */}
      <div className="mb-2 flex items-center gap-3">
        <span className="font-pixel text-sm" style={{ color: "var(--px-text-dim)" }}>
          HP
        </span>
        <span className="font-pixel text-base" style={{ color: "var(--px-text)" }}>
          {hp}
          <span style={{ color: "var(--px-text-dim)", fontSize: "0.75rem" }}>/{maxHp}</span>
        </span>
      </div>

      {/* Bar track */}
      <div className="px-bar-track overflow-hidden" style={{ height: 16, width: "min(240px, 60vw)" }}>
        <div
          style={{
            height: "100%",
            width: `${pct}%`,
            background: barColor,
            transition: "width 0.4s steps(8), background-color 0.3s",
            imageRendering: "pixelated",
          }}
        />
      </div>
    </div>
  );
}
