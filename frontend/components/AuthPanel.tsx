"use client";

import { useEffect, useState } from "react";
import { type User } from "firebase/auth";
import { signInWithGoogle, signOut, onAuthStateChanged } from "../lib/firebase";

type Props = {
  onAuthChange: (user: User | null) => void;
};

export default function AuthPanel({ onAuthChange }: Props) {
  const [user, setUser] = useState<User | null | "loading">("loading");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged((u) => {
      setUser(u);
      onAuthChange(u);
    });
    return unsubscribe;
  }, [onAuthChange]);

  async function handleSignIn() {
    setBusy(true);
    setError(null);
    try {
      await signInWithGoogle();
    } catch (e: unknown) {
      const code = (e as { code?: string }).code;
      if (code !== "auth/popup-closed-by-user" && code !== "auth/cancelled-popup-request") {
        setError(e instanceof Error ? e.message : "Sign-in failed.");
      }
    } finally {
      setBusy(false);
    }
  }

  async function handleSignOut() {
    setBusy(true);
    setError(null);
    try {
      await signOut();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sign-out failed.");
    } finally {
      setBusy(false);
    }
  }

  const panelStyle = {
    background: "var(--px-panel)",
    border: "2px solid var(--px-panel-border)",
    boxShadow: "4px 4px 0 #1d0a1a",
    padding: "24px",
  };

  if (user === "loading") {
    return (
      <div style={panelStyle}>
        <p className="font-pixel text-sm" style={{ color: "var(--px-text-dim)" }}>
          …
        </p>
      </div>
    );
  }

  if (user && !user.isAnonymous) {
    return (
      <div style={panelStyle} className="flex flex-col gap-4">
        <p
          className="font-pixel text-sm"
          style={{ color: "var(--px-text-dim)", letterSpacing: "0.06em" }}
        >
          SIGNED IN
        </p>
        <p className="font-pixel text-sm" style={{ color: "var(--px-gold)" }}>
          {user.displayName ?? user.email ?? "Google account"}
        </p>
        <p className="font-pixel text-xs" style={{ color: "var(--px-text-dim)", lineHeight: 2 }}>
          Progress is saved between sessions.
        </p>
        <button
          onClick={handleSignOut}
          disabled={busy}
          className="font-pixel text-sm"
          style={{
            background: "transparent",
            border: "2px solid var(--px-panel-border)",
            color: "var(--px-text-dim)",
            padding: "8px 14px",
            cursor: busy ? "not-allowed" : "pointer",
            opacity: busy ? 0.5 : 1,
          }}
        >
          {busy ? "…" : "Sign out"}
        </button>
      </div>
    );
  }

  // Not signed in
  return (
    <div style={panelStyle} className="flex flex-col gap-4">
      <p
        className="font-pixel text-sm"
        style={{ color: "var(--px-text-dim)", letterSpacing: "0.06em" }}
      >
        SIGN IN (OPTIONAL)
      </p>
      <p className="font-pixel text-xs" style={{ color: "var(--px-text-dim)", lineHeight: 2 }}>
        Sign in to save your progress across sessions. Otherwise, play as guest, but history is lost
        when you quit.
      </p>

      {error && (
        <p
          className="font-pixel text-xs p-3"
          style={{
            background: "rgba(120,20,20,0.6)",
            border: "2px solid #e05050",
            color: "#f8a0a0",
          }}
        >
          {error}
        </p>
      )}

      <button
        onClick={handleSignIn}
        disabled={busy}
        className="font-pixel text-sm"
        style={{
          background: "rgba(255,255,255,0.06)",
          border: "2px solid var(--px-panel-border)",
          color: "var(--px-text)",
          padding: "12px 16px",
          cursor: busy ? "not-allowed" : "pointer",
          opacity: busy ? 0.5 : 1,
        }}
      >
        {busy ? "Opening…" : "▶  Sign in with Google"}
      </button>
    </div>
  );
}
