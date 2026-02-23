"use client";

import { useRef, useState, useCallback, useEffect, forwardRef, useImperativeHandle } from "react";
import type { Point, Stroke } from "../lib/types";

export type DrawingCanvasHandle = {
  getStrokes: () => Stroke[];
  clear: () => void;
};

const DrawingCanvas = forwardRef<DrawingCanvasHandle, object>(function DrawingCanvas(_, ref) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const drawing = useRef(false);
  const currentStroke = useRef<Point[]>([]);
  const [strokes, setStrokes] = useState<Stroke[]>([]);

  // Keep canvas resolution in sync with its CSS size.
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ro = new ResizeObserver(() => {
      const { width, height } = canvas.getBoundingClientRect();
      canvas.width = Math.round(width);
      canvas.height = Math.round(height);

      // Context settings are reset on resize — reapply.
      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.lineWidth = 3;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.strokeStyle = "#1e293b";
      }
    });
    ro.observe(canvas);
    return () => ro.disconnect();
  }, []);

  function getPos(e: React.MouseEvent<HTMLCanvasElement>): Point {
    const r = canvasRef.current!.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  }

  function onMouseDown(e: React.MouseEvent<HTMLCanvasElement>) {
    drawing.current = true;
    const p = getPos(e);
    currentStroke.current = [p];
    const ctx = canvasRef.current?.getContext("2d");
    ctx?.beginPath();
    ctx?.moveTo(p.x, p.y);
  }

  function onMouseMove(e: React.MouseEvent<HTMLCanvasElement>) {
    if (!drawing.current) return;
    const p = getPos(e);
    currentStroke.current.push(p);
    const ctx = canvasRef.current?.getContext("2d");
    ctx?.lineTo(p.x, p.y);
    ctx?.stroke();
  }

  function onMouseUp() {
    if (!drawing.current) return;
    drawing.current = false;
    const pts = currentStroke.current;
    if (pts.length > 1) setStrokes((s) => [...s, { points: [...pts], timestamp_ms: Date.now() }]);
    currentStroke.current = [];
  }

  const clear = useCallback(() => {
    const canvas = canvasRef.current;
    if (canvas) canvas.getContext("2d")?.clearRect(0, 0, canvas.width, canvas.height);
    setStrokes([]);
    currentStroke.current = [];
  }, []);

  useImperativeHandle(ref, () => ({ getStrokes: () => strokes, clear }), [strokes, clear]);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%", background: "#f5f0f8" }}>
      <canvas
        ref={canvasRef}
        style={{ display: "block", width: "100%", height: "100%", cursor: "crosshair" }}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
      />
      <button
        type="button"
        onClick={clear}
        className="font-pixel"
        style={{
          position: "absolute",
          right: 8,
          top: 8,
          background: "rgba(29,10,26,0.75)",
          border: "2px solid var(--px-panel-border)",
          color: "var(--px-text-dim)",
          padding: "4px 10px",
          fontSize: "0.55rem",
          cursor: "pointer",
        }}
      >
        Clear
      </button>
    </div>
  );
});

export default DrawingCanvas;
