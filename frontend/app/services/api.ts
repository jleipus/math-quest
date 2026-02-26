import { Task, Stroke, AnalysisResult, Difficulty } from "../types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

export type GenerateTasksRequest = {
  topic: string;
  difficulty: Difficulty;
  count: number;
};

export type AnalyseRequest = {
  task_id: string;
  content: string; // JSON-serialised stroke array
};

export type ApiResponse<T> = {
  data: T | null;
  error: {
    code: string;
    message: string;
  } | null;
};

export async function generateTasks(
  request: GenerateTasksRequest,
): Promise<Task[]> {
  const response = await fetch(`${API_BASE_URL}/tasks/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error("Failed to generate tasks");
  }

  const result: ApiResponse<{ tasks: Task[] }> = await response.json();

  if (result.error) {
    throw new Error(result.error.message);
  }

  return result.data?.tasks || [];
}

export async function analyseAnswer(
  taskId: string,
  strokes: Stroke[],
  signal?: AbortSignal,
): Promise<AnalysisResult> {
  const response = await fetch(`${API_BASE_URL}/assistant/analyse`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    signal,
    body: JSON.stringify({
      task_id: taskId,
      content: JSON.stringify(strokes),
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to analyze answer");
  }

  const result: ApiResponse<AnalysisResult> = await response.json();

  if (result.error) {
    throw new Error(result.error.message);
  }

  if (result.data) {
    return result.data;
  }

  throw new Error("No data returned from analysis");
}
