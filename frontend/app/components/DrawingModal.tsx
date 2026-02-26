"use client";

import { useRef, useEffect, useState } from "react";
import { Card, Point, Stroke } from "../types";

type FeedbackVariant = "issue" | "clearer" | "success";

type DrawingModalProps = {
  card: Card;
  onClose: () => void;
  onSubmit: (strokes: Stroke[]) => void;
  isSubmitting: boolean;
  feedback: string | null;
  feedbackVariant: FeedbackVariant;
};

export default function DrawingModal({
  card,
  onClose,
  onSubmit,
  isSubmitting,
  feedback,
  feedbackVariant,
}: DrawingModalProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null);
  const currentStrokeRef = useRef<Point[]>([]);
  const isDrawingRef = useRef(false);
  const strokesRef = useRef<Stroke[]>([]);
  const devicePixelRatioRef = useRef(1);

  const drawStroke = (ctx: CanvasRenderingContext2D, points: Point[]) => {
    if (points.length === 0) return;

    if (points.length === 1) {
      const point = points[0];
      ctx.beginPath();
      ctx.arc(point.x, point.y, 2, 0, Math.PI * 2);
      ctx.fillStyle = "#ffffff";
      ctx.fill();
      return;
    }

    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let index = 1; index < points.length; index++) {
      ctx.lineTo(points[index].x, points[index].y);
    }
    ctx.stroke();
  };

  const configureCanvas = () => {
    if (!canvasRef.current || !containerRef.current) return;

    const container = containerRef.current;
    const rect = container.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const displayWidth = rect.width;
    const displayHeight = rect.height;

    canvasRef.current.style.width = `${displayWidth}px`;
    canvasRef.current.style.height = `${displayHeight}px`;
    canvasRef.current.width = Math.round(displayWidth * dpr);
    canvasRef.current.height = Math.round(displayHeight * dpr);

    const ctx = canvasRef.current.getContext("2d");
    if (!ctx) return;

    devicePixelRatioRef.current = dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    ctx.lineWidth = 4;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = "#ffffff";
    ctx.fillStyle = "#ffffff";
    ctxRef.current = ctx;
  };

  const redrawCanvas = () => {
    const canvas = canvasRef.current;
    const ctx = ctxRef.current;
    if (!canvas || !ctx) return;

    const dpr = devicePixelRatioRef.current || 1;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    strokesRef.current.forEach((stroke) => {
      drawStroke(ctx, stroke.points);
    });

    if (currentStrokeRef.current.length > 0) {
      drawStroke(ctx, currentStrokeRef.current);
    }
  };

  useEffect(() => {
    const resizeCanvas = () => {
      configureCanvas();
      redrawCanvas();
    };

    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    const timeout = setTimeout(resizeCanvas, 100);

    return () => {
      window.removeEventListener("resize", resizeCanvas);
      clearTimeout(timeout);
    };
  }, []);

  const getPointerPos = (e: React.PointerEvent<HTMLCanvasElement>): Point => {
    if (!canvasRef.current) return { x: 0, y: 0 };
    const rect = canvasRef.current.getBoundingClientRect();

    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };
  };

  const startDrawing = (e: React.PointerEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const firstPoint = getPointerPos(e);
    e.currentTarget.setPointerCapture(e.pointerId);

    isDrawingRef.current = true;
    currentStrokeRef.current = [firstPoint];
    redrawCanvas();
  };

  const draw = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!isDrawingRef.current || !ctxRef.current) return;
    e.preventDefault();

    const pos = getPointerPos(e);

    currentStrokeRef.current = [...currentStrokeRef.current, pos];

    redrawCanvas();
  };

  const stopDrawing = (e?: React.PointerEvent<HTMLCanvasElement>) => {
    if (e) {
      e.preventDefault();
      if (e.currentTarget.hasPointerCapture(e.pointerId)) {
        e.currentTarget.releasePointerCapture(e.pointerId);
      }
    }

    if (!isDrawingRef.current) return;

    isDrawingRef.current = false;

    if (currentStrokeRef.current.length > 0) {
      const committedStroke: Stroke = {
        points: [...currentStrokeRef.current],
        timestamp_ms: Date.now(),
      };
      strokesRef.current = [...strokesRef.current, committedStroke];
      currentStrokeRef.current = [];
      redrawCanvas();
    }
  };

  const clearCanvas = () => {
    strokesRef.current = [];
    currentStrokeRef.current = [];
    redrawCanvas();
    isDrawingRef.current = false;
  };

  const handleSubmit = () => {
    if (strokesRef.current.length === 0) {
      alert("Please draw your answer first!");
      return;
    }
    onSubmit(strokesRef.current);
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
          <div
            className={`mb-4 animate-fade-in rounded-xl border-2 p-4 text-center text-lg font-semibold text-white shadow-lg ${
              feedbackVariant === "issue"
                ? "border-red-400 bg-gradient-to-r from-red-600 to-rose-500"
                : feedbackVariant === "success"
                  ? "border-emerald-400 bg-gradient-to-r from-emerald-600 to-green-500"
                  : "border-amber-400 bg-gradient-to-r from-amber-600 to-yellow-500"
            }`}
          >
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
            onPointerDown={startDrawing}
            onPointerMove={draw}
            onPointerUp={stopDrawing}
            onPointerCancel={stopDrawing}
            onPointerLeave={stopDrawing}
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
