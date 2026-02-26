"use client";

import {
  useRef,
  useState,
  useCallback,
  useEffect,
  forwardRef,
  useImperativeHandle,
  useLayoutEffect,
} from "react";
import type { Point, Stroke } from "../lib/types";

export type DrawingCanvasHandle = {
  getStrokes: () => Stroke[];
  clear: () => void;
};

type Props = {
  initialStrokes?: Stroke[];
};

const DrawingCanvas = forwardRef<DrawingCanvasHandle, Props>(function DrawingCanvas(
  { initialStrokes },
  ref,
) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const drawing = useRef(false);
  const currentStroke = useRef<Point[]>([]);
  const [strokes, setStrokes] = useState<Stroke[]>(initialStrokes ?? []);
  // Mirror of strokes in a ref so the ResizeObserver closure always reads
  // the current value without going through stale React state.
  const strokesRef = useRef<Stroke[]>(initialStrokes ?? []);

  function getCtx() {
    const ctx = canvasRef.current?.getContext("2d");
    if (ctx) {
      ctx.lineWidth = 3;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.strokeStyle = "#1e293b";
    }
    return ctx ?? null;
  }

  // Keep strokesRef in sync (runs before paint, so the ResizeObserver never reads stale data).
  useLayoutEffect(() => {
    strokesRef.current = strokes;
  }, [strokes]);

  function redraw(strokeList: Stroke[]) {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = getCtx();
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (const stroke of strokeList) {
      if (stroke.points.length < 2) continue;
      ctx.beginPath();
      ctx.moveTo(stroke.points[0].x, stroke.points[0].y);
      for (const p of stroke.points.slice(1)) ctx.lineTo(p.x, p.y);
      ctx.stroke();
    }
  }

  // Keep canvas resolution in sync with its CSS size.
  // Also redraws after initial sizing so restored strokes appear immediately.
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ro = new ResizeObserver(() => {
      const { width, height } = canvas.getBoundingClientRect();
      const w = Math.round(width);
      const h = Math.round(height);
      // Assigning canvas.width/height clears the bitmap — only do it when the
      // size actually changed (avoids wiping strokes on layout micro-updates).
      if (canvas.width === w && canvas.height === h) return;
      canvas.width = w;
      canvas.height = h;
      // Use the ref so we always have the current stroke list, even if a
      // stroke is in progress and hasn't been committed to React state yet.
      redraw(strokesRef.current);
      // Also redraw the in-progress stroke so it isn't visually wiped.
      const pts = currentStroke.current;
      if (pts.length >= 2) {
        const ctx = getCtx();
        if (ctx) {
          ctx.beginPath();
          ctx.moveTo(pts[0].x, pts[0].y);
          for (const p of pts.slice(1)) ctx.lineTo(p.x, p.y);
          ctx.stroke();
        }
      }
    });
    ro.observe(canvas);
    return () => ro.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function getPos(e: React.MouseEvent<HTMLCanvasElement>): Point {
    const r = canvasRef.current!.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  }

  function onMouseDown(e: React.MouseEvent<HTMLCanvasElement>) {
    drawing.current = true;
    const p = getPos(e);
    currentStroke.current = [p];
    const ctx = getCtx();
    ctx?.beginPath();
    ctx?.moveTo(p.x, p.y);
  }

  function onMouseMove(e: React.MouseEvent<HTMLCanvasElement>) {
    if (!drawing.current) return;
    const p = getPos(e);
    currentStroke.current.push(p);
    const ctx = getCtx();
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

  const undo = useCallback(() => {
    setStrokes((prev) => {
      const next = prev.slice(0, -1);
      redraw(next);
      return next;
    });
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
      <div style={{ position: "absolute", right: 8, top: 8, display: "flex", gap: 6 }}>
        <button
          type="button"
          onClick={undo}
          disabled={strokes.length === 0}
          className="font-pixel"
          style={{
            background: "rgba(29,10,26,0.75)",
            border: "2px solid var(--px-panel-border)",
            color: strokes.length === 0 ? "rgba(255,255,255,0.2)" : "var(--px-text-dim)",
            padding: "4px 10px",
            fontSize: "0.55rem",
            cursor: strokes.length === 0 ? "not-allowed" : "pointer",
          }}
        >
          Undo
        </button>
        <button
          type="button"
          onClick={clear}
          disabled={strokes.length === 0}
          className="font-pixel"
          style={{
            background: "rgba(29,10,26,0.75)",
            border: "2px solid var(--px-panel-border)",
            color: strokes.length === 0 ? "rgba(255,255,255,0.2)" : "var(--px-text-dim)",
            padding: "4px 10px",
            fontSize: "0.55rem",
            cursor: strokes.length === 0 ? "not-allowed" : "pointer",
          }}
        >
          Clear
        </button>
      </div>
    </div>
  );
});

export default DrawingCanvas;
