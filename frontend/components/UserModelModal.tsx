"use client";

import { useEffect } from "react";
import UserProfile from "./UserProfile";

type Props = {
  onClose: () => void;
};

export default function UserModelModal({ onClose }: Props) {
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  const closeButton = (
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
  );

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
        <UserProfile showReset actions={closeButton} />
      </div>
    </div>
  );
}
