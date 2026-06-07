"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useGame } from "../lib/gameContext";

type Props = {
  onResume: () => void;
};

export default function PauseMenu({ onResume }: Props) {
  const router = useRouter();
  const { reset } = useGame();

  // Close on Escape
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onResume();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onResume]);

  function handleQuit() {
    reset();
    router.push("/");
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(10,0,8,0.85)", backdropFilter: "blur(4px)" }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onResume();
      }}
    >
      <div
        className="flex flex-col gap-6"
        style={{
          width: 360,
          background: "#1d0a1a",
          border: "3px solid var(--px-panel-border)",
          boxShadow: "8px 8px 0 #0a0008",
          padding: "40px 36px",
        }}
      >
        {/* Resume */}
        <button onClick={onResume} className="px-btn w-full py-4 text-sm">
          Fortsätt
        </button>

        {/* Quit to start page */}
        <button
          onClick={handleQuit}
          className="font-pixel w-full py-4 text-sm"
          style={{
            background: "rgba(60,30,60,0.7)",
            border: "2px solid var(--px-panel-border)",
            color: "var(--px-text)",
            letterSpacing: "0.06em",
            cursor: "pointer",
            boxShadow: "3px 3px 0 #0a0008",
          }}
        >
          Avsluta till start
        </button>
      </div>
    </div>
  );
}
