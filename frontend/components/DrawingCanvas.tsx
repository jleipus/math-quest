"use client";

import { useRef, useEffect, useState, useCallback, forwardRef, useImperativeHandle } from "react";
import type { Point, Stroke } from "../lib/types";

export type DrawingCanvasHandle = {
  getStrokes: () => Stroke[];
  clear: () => void;
};

type Props = {
  width?: number;
  height?: number;
};

const DrawingCanvas = forwardRef<DrawingCanvasHandle, Props>(function DrawingCanvas(
  _props,
  ref,
) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null);
  const isDrawingRef = useRef(false);
  const currentStrokeRef = useRef<Point[]>([]);
  const [strokes, setStrokes] = useState<Stroke[]>([]);

  // Keep canvas buffer size = rendered size so mouse coords always line up
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const syncSize = () => {
      const { width, height } = canvas.getBoundingClientRect();
      if (canvas.width !== Math.round(width) || canvas.height !== Math.round(height)) {
        canvas.width = Math.round(width);
        canvas.height = Math.round(height);
        // Re-apply context settings after resize (context state is reset)
        const ctx = canvas.getContext("2d");
        if (ctx) {
          ctx.lineWidth = 3;
          ctx.lineCap = "round";
          ctx.lineJoin = "round";
          ctx.strokeStyle = "#1e293b";
          ctxRef.current = ctx;
        }
      }
    };

    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.lineWidth = 3;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = "#1e293b";
    ctxRef.current = ctx;

    syncSize();
    const ro = new ResizeObserver(syncSize);
    ro.observe(canvas);
    return () => ro.disconnect();
  }, []);

  // Mouse position relative to canvas buffer (accounts for CSS scaling)
  const getPos = (e: React.MouseEvent<HTMLCanvasElement>): Point => {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY,
    };
  };

  const startDraw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    isDrawingRef.current = true;
    const pos = getPos(e);
    currentStrokeRef.current = [pos];
    const ctx = ctxRef.current;
    if (!ctx) return;
    ctx.beginPath();
    ctx.moveTo(pos.x, pos.y);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawingRef.current || !ctxRef.current) return;
    const pos = getPos(e);
    currentStrokeRef.current.push(pos);
    ctxRef.current.lineTo(pos.x, pos.y);
    ctxRef.current.stroke();
  };

  const endDraw = () => {
    if (!isDrawingRef.current) return;
    isDrawingRef.current = false;
    const pts = currentStrokeRef.current;
    if (pts.length > 1) {
      setStrokes((prev) => [...prev, { points: [...pts], timestamp_ms: Date.now() }]);
    }
    currentStrokeRef.current = [];
  };

  const clear = useCallback(() => {
    const canvas = canvasRef.current;
    const ctx = ctxRef.current;
    if (!canvas || !ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setStrokes([]);
    currentStrokeRef.current = [];
  }, []);

  useImperativeHandle(ref, () => ({ getStrokes: () => strokes, clear }), [strokes, clear]);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%", background: "#f5f0f8", overflow: "hidden" }}>
      <canvas
        ref={canvasRef}
        style={{ display: "block", cursor: "crosshair", width: "100%", height: "100%" }}
        onMouseDown={startDraw}
        onMouseMove={draw}
        onMouseUp={endDraw}
        onMouseLeave={endDraw}
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
