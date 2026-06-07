"use client";

import { useState, useEffect, useRef } from "react";

type Step = {
  /** Which element to highlight */
  selector: string;
  title: string;
  body: string;
  /** Which side of the element to place the tooltip */
  side: "bottom" | "top" | "left" | "right";
};

const STEPS: Step[] = [
  {
    selector: "[data-tutorial='player-hp']",
    title: "Dina HP",
    body: "Det här är din hälsobar. Om den når noll är spelet slut. Återställ hälsa med helakort.",
    side: "bottom",
  },
  {
    selector: "[data-tutorial='enemy']",
    title: "Fiende",
    body: "Besegra fienden genom att reducera dess HP till noll med attackkort. Siffran ovanför visar hur mycket skada den kommer att ge dig i slutet av rundan.",
    side: "bottom",
  },
  {
    selector: "[data-tutorial='profile-btn']",
    title: "Din profil",
    body: "Spårar dina prestationer inom olika ämnen och svårighetsgrader. Spelet använder detta för att anpassa korten du får.",
    side: "left",
  },
  {
    selector: "[data-tutorial='hand']",
    title: "Dina kort",
    body: "Varje kort har en matematikuppgift. Klicka på ett kort för att öppna det, lös uppgiften och spela sedan kortet. Kort kostar energi, visas av prickarna ovan. Felaktiga svar minskar kortets styrka.",
    side: "top",
  },
  {
    selector: "[data-tutorial='end-turn']",
    title: "Avsluta runda",
    body: "När du är klar med att spela kort, tryck på Avsluta runda. Fienden attackerar, din energi fylls på och du får en ny hand.",
    side: "top",
  },
];

function getRect(selector: string): DOMRect | null {
  const el = document.querySelector(selector);
  return el ? el.getBoundingClientRect() : null;
}

const PAD = 10; // Padding around the highlighted element

export default function TutorialOverlay({ onDone }: { onDone: () => void }) {
  const [step, setStep] = useState(0);
  const [rect, setRect] = useState<DOMRect | null>(null);
  const [visible, setVisible] = useState(false);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const current = STEPS[step];

  // Measure target element whenever step changes
  useEffect(() => {
    function measure() {
      const r = getRect(current.selector);
      setRect(r);
      // Small delay so the tooltip renders before we show it (avoids flash)
      setTimeout(() => setVisible(true), 30);
    }
    setVisible(false);
    // RAF so the DOM has settled after any layout changes
    const id = requestAnimationFrame(measure);
    return () => cancelAnimationFrame(id);
  }, [step, current.selector]);

  // Also re-measure on resize
  useEffect(() => {
    function onResize() {
      setRect(getRect(current.selector));
    }
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [current.selector]);

  function finish() {
    onDone();
  }

  function next() {
    if (step < STEPS.length - 1) {
      setStep((s) => s + 1);
    } else {
      finish();
    }
  }

  // Highlight rectangle (with padding)
  const hx = rect ? rect.left - PAD : 0;
  const hy = rect ? rect.top - PAD : 0;
  const hw = rect ? rect.width + PAD * 2 : 0;
  const hh = rect ? rect.height + PAD * 2 : 0;

  // Tooltip position
  function tooltipStyle(): React.CSSProperties {
    if (!rect) return { top: "50%", left: "50%", transform: "translate(-50%,-50%)" };

    const side = current.side;
    const GAP = 18;
    const base: React.CSSProperties = {
      position: "fixed",
      zIndex: 10001,
      maxWidth: "min(320px, calc(100vw - 24px))",
    };

    if (side === "bottom") {
      return { ...base, top: hy + hh + GAP, left: hx + hw / 2, transform: "translateX(-50%)" };
    }
    if (side === "top") {
      return {
        ...base,
        bottom: window.innerHeight - hy + GAP,
        left: hx + hw / 2,
        transform: "translateX(-50%)",
      };
    }
    if (side === "left") {
      return {
        ...base,
        top: hy + hh / 2,
        right: window.innerWidth - hx + GAP,
        transform: "translateY(-50%)",
      };
    }
    // right
    return { ...base, top: hy + hh / 2, left: hx + hw + GAP, transform: "translateY(-50%)" };
  }

  // Arrow pointing from tooltip toward the element
  function arrowStyle(): React.CSSProperties {
    const side = current.side;
    const base: React.CSSProperties = {
      position: "absolute",
      width: 0,
      height: 0,
    };
    const color = "#c89e2a";
    if (side === "bottom") {
      return {
        ...base,
        top: -10,
        left: "50%",
        transform: "translateX(-50%)",
        borderLeft: "10px solid transparent",
        borderRight: "10px solid transparent",
        borderBottom: `10px solid ${color}`,
      };
    }
    if (side === "top") {
      return {
        ...base,
        bottom: -10,
        left: "50%",
        transform: "translateX(-50%)",
        borderLeft: "10px solid transparent",
        borderRight: "10px solid transparent",
        borderTop: `10px solid ${color}`,
      };
    }
    if (side === "left") {
      return {
        ...base,
        top: "50%",
        right: -10,
        transform: "translateY(-50%)",
        borderTop: "10px solid transparent",
        borderBottom: "10px solid transparent",
        borderLeft: `10px solid ${color}`,
      };
    }
    // right
    return {
      ...base,
      top: "50%",
      left: -10,
      transform: "translateY(-50%)",
      borderTop: "10px solid transparent",
      borderBottom: "10px solid transparent",
      borderRight: `10px solid ${color}`,
    };
  }

  return (
    <>
      {/* Dark overlay with a cut-out hole over the highlighted element, via SVG */}
      <svg
        style={{
          position: "fixed",
          inset: 0,
          width: "100vw",
          height: "100dvh",
          zIndex: 10000,
          pointerEvents: "none",
        }}
      >
        <defs>
          <mask id="tutorial-mask">
            {/* White = visible overlay */}
            <rect width="100%" height="100%" fill="white" />
            {/* Black = cut-out (transparent in the mask result) */}
            {rect && <rect x={hx} y={hy} width={hw} height={hh} rx={4} fill="black" />}
          </mask>
        </defs>
        <rect width="100%" height="100%" fill="rgba(0,0,0,0.78)" mask="url(#tutorial-mask)" />
        {/* Gold border around highlight */}
        {rect && (
          <rect
            x={hx}
            y={hy}
            width={hw}
            height={hh}
            rx={4}
            fill="none"
            stroke="#c89e2a"
            strokeWidth={2}
          />
        )}
      </svg>

      {/* Tooltip */}
      <div
        ref={tooltipRef}
        style={{
          ...tooltipStyle(),
          opacity: visible ? 1 : 0,
          transition: "opacity 0.15s",
          background: "#1d0a1a",
          border: "2px solid #c89e2a",
          boxShadow: "4px 4px 0 #0a0008",
          padding: "20px 22px 16px",
          zIndex: 10001,
        }}
      >
        {/* Arrow */}
        <div style={arrowStyle()} />

        {/* Step counter */}
        <div
          className="font-pixel"
          style={{
            fontSize: "0.6rem",
            color: "var(--px-text-dim)",
            marginBottom: 6,
            letterSpacing: "0.08em",
          }}
        >
          {step + 1} / {STEPS.length}
        </div>

        {/* Title */}
        <div
          className="font-pixel"
          style={{ fontSize: "0.9rem", color: "#c89e2a", marginBottom: 10, lineHeight: 1.4 }}
        >
          {current.title}
        </div>

        {/* Body */}
        <p
          className="font-pixel"
          style={{ fontSize: "0.7rem", color: "var(--px-text)", lineHeight: 1.8, marginBottom: 16 }}
        >
          {current.body}
        </p>

        {/* Buttons */}
        <div className="flex items-center justify-between gap-3">
          <button
            onClick={finish}
            className="font-pixel"
            style={{
              fontSize: "0.65rem",
              color: "var(--px-text-dim)",
              background: "transparent",
              border: "none",
              cursor: "pointer",
              textDecoration: "underline",
              padding: 0,
            }}
          >
            Hoppa över
          </button>
          <button
            onClick={next}
            className="px-btn font-pixel"
            style={{ fontSize: "0.75rem", padding: "8px 20px" }}
          >
            {step < STEPS.length - 1 ? "Nästa >" : "Förstått!"}
          </button>
        </div>
      </div>
    </>
  );
}
