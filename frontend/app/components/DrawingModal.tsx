"use client";

import { useRef, useEffect, useState } from "react";
import { Card, Point, Stroke } from "../types";

type DrawingModalProps = {
  card: Card;
  onClose: () => void;
  onSubmit: (strokes: Stroke[]) => void;
  isSubmitting: boolean;
  feedback: string | null;
};

export default function DrawingModal({
  card,
  onClose,
  onSubmit,
  isSubmitting,
  feedback,
}: DrawingModalProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [strokes, setStrokes] = useState<Stroke[]>([]);
  const [currentStroke, setCurrentStroke] = useState<Point[]>([]);

  useEffect(() => {
    const resizeCanvas = () => {
      if (canvasRef.current && containerRef.current) {
        const container = containerRef.current;
        const rect = container.getBoundingClientRect();

        canvasRef.current.width = rect.width;
        canvasRef.current.height = rect.height;

        const ctx = canvasRef.current.getContext("2d");
        if (ctx) {
          ctx.lineWidth = 4;
          ctx.lineCap = "round";
          ctx.lineJoin = "round";
          ctx.strokeStyle = "#ffffff";
          ctxRef.current = ctx;
        }

        // Redraw all strokes after resize
        if (ctx && strokes.length > 0) {
          strokes.forEach((stroke) => {
            if (stroke.points.length > 1) {
              ctx.beginPath();
              ctx.moveTo(stroke.points[0].x, stroke.points[0].y);
              for (let i = 1; i < stroke.points.length; i++) {
                ctx.lineTo(stroke.points[i].x, stroke.points[i].y);
              }
              ctx.stroke();
            }
          });
        }
      }
    };

    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    const timeout = setTimeout(resizeCanvas, 100);

    return () => {
      window.removeEventListener("resize", resizeCanvas);
      clearTimeout(timeout);
    };
  }, [strokes]);

  const getMousePos = (e: React.MouseEvent<HTMLCanvasElement>): Point => {
    if (!canvasRef.current) return { x: 0, y: 0 };
    const rect = canvasRef.current.getBoundingClientRect();

    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };
  };

  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDrawing(true);
    setCurrentStroke([getMousePos(e)]);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !ctxRef.current) return;

    const pos = getMousePos(e);
    setCurrentStroke((prev) => [...prev, pos]);

    const ctx = ctxRef.current;
    ctx.beginPath();
    ctx.moveTo(
      currentStroke[currentStroke.length - 1].x,
      currentStroke[currentStroke.length - 1].y,
    );
    ctx.lineTo(pos.x, pos.y);
    ctx.stroke();
  };

  const stopDrawing = () => {
    if (isDrawing && currentStroke.length > 0) {
      setStrokes((prev) => [
        ...prev,
        {
          points: [...currentStroke],
          timestamp_ms: Date.now(),
        },
      ]);
      setCurrentStroke([]);
    }
    setIsDrawing(false);
  };

  const clearCanvas = () => {
    if (ctxRef.current && canvasRef.current) {
      ctxRef.current.clearRect(
        0,
        0,
        canvasRef.current.width,
        canvasRef.current.height,
      );
    }
    setStrokes([]);
    setCurrentStroke([]);
  };

  const handleSubmit = () => {
    if (strokes.length === 0) {
      alert("Please draw your answer first!");
      return;
    }
    onSubmit(strokes);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-4 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="flex h-[95vh] w-[95vw] max-w-[1600px] flex-col rounded-2xl border-4 border-purple-500 bg-gradient-to-br from-slate-800 via-slate-900 to-slate-800 p-8 shadow-2xl shadow-purple-500/30">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <div className="mb-1 text-sm font-semibold uppercase tracking-wider text-purple-400">
              Challenge
            </div>
            <h2 className="text-4xl font-bold text-white drop-shadow-lg">
              Solve: <span className="text-purple-400">{card.question}</span>
            </h2>
            <p className="mt-2 text-gray-400">
              Draw your solution step by step
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg bg-red-600 px-6 py-3 font-semibold text-white shadow-lg transition hover:bg-red-700 hover:shadow-xl active:scale-95"
          >
            ✖ Close
          </button>
        </div>

        {/* Feedback */}
        {feedback && (
          <div className="mb-4 animate-fade-in rounded-xl border-2 border-blue-400 bg-gradient-to-r from-blue-600 to-blue-500 p-4 text-center text-lg font-semibold text-white shadow-lg">
            {feedback}
          </div>
        )}

        {/* Canvas */}
        <div
          ref={containerRef}
          className="mb-6 flex-1 overflow-hidden rounded-xl border-4 border-gray-700 bg-slate-950 shadow-2xl shadow-black/50"
        >
          <canvas
            ref={canvasRef}
            className="h-full w-full cursor-crosshair"
            onMouseDown={startDrawing}
            onMouseMove={draw}
            onMouseUp={stopDrawing}
            onMouseLeave={stopDrawing}
          />
        </div>

        {/* Controls */}
        <div className="flex gap-4">
          <button
            onClick={clearCanvas}
            className="rounded-xl bg-gray-700 px-8 py-4 font-semibold text-white shadow-lg transition hover:bg-gray-600 hover:shadow-xl active:scale-95"
          >
            🗑️ Clear
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="flex-1 rounded-xl bg-gradient-to-r from-green-600 to-emerald-600 px-8 py-4 font-bold text-white shadow-lg transition hover:from-green-500 hover:to-emerald-500 hover:shadow-xl active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <span className="flex items-center justify-center gap-2">
                <span className="animate-spin">⏳</span> Analyzing...
              </span>
            ) : (
              "✓ Submit Answer"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
