"use client";

import Image from "next/image";

type Props = {
  hp: number;
  maxHP: number;
  shake: boolean;
  nextDamage: number;
};

export default function EnemyDisplay({ hp, maxHP: maxHp, shake, nextDamage }: Props) {
  const health_pct = Math.max(0, Math.min(100, (hp / maxHp) * 100));

  return (
    <div className="flex flex-col items-center gap-3">
      {/* Incoming attack warning */}
      {nextDamage > 0 && (
        <div
          className="font-pixel text-center text-sm"
          style={{
            background: "rgba(100,20,20,0.75)",
            border: "2px solid #e05050",
            boxShadow: "3px 3px 0 #0a0008",
            padding: "6px 18px",
            color: "#ff9090",
            lineHeight: 1.8,
          }}
        >
          ⚠ Incoming: {nextDamage} dmg
        </div>
      )}

      {/* Sprite box */}
      <div
        className={shake ? "animate-shake" : ""}
        style={{
          width: 120,
          height: 120,
          background: "var(--px-panel)",
          border: "3px solid #e05050",
          boxShadow: "4px 4px 0 #1d0a1a, 0 0 20px rgba(224,80,80,0.3)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          imageRendering: "pixelated",
        }}
        aria-label="Enemy"
      >
        <Image
          src="/assets/items/skull.png"
          alt="Enemy"
          width={80}
          height={80}
          style={{ imageRendering: "pixelated" }}
        />
      </div>

      {/* HP numbers */}
      <div
        style={{
          background: "rgba(10,0,8,0.75)",
          border: "2px solid #4a1a1a",
          boxShadow: "3px 3px 0 #0a0008",
          padding: "8px 14px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 6,
          width: 200,
        }}
      >
        <div
          className="font-pixel text-base"
          style={{ color: "#ff9090", textShadow: "2px 2px 0 #0a0008" }}
        >
          {hp}
          <span style={{ color: "#884444", fontSize: "0.75rem" }}>/{maxHp}</span>
        </div>
        <div className="px-bar-track overflow-hidden" style={{ height: 14, width: "100%" }}>
          <div
            style={{
              height: "100%",
              width: `${health_pct}%`,
              background: "#e05050",
              transition: "width 0.4s steps(8)",
              imageRendering: "pixelated",
            }}
          />
        </div>
      </div>
    </div>
  );
}
