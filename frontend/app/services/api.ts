import { Task, Difficulty, Stroke, AnalysisResult } from "../types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

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
  try {
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
  } catch (error) {
    console.error("Error generating tasks:", error);

    // Placeholder logic until API is available
    return generatePlaceholderTasks(request);
  }
}

function generatePlaceholderTasks(request: GenerateTasksRequest): Task[] {
  const placeholders: Record<Difficulty, Task[]> = {
    easy: [
      {
        task_id: "placeholder_easy_1",
        question: "2 + 2",
        expected_answer: "4",
        topic: request.topic,
        difficulty: "easy",
      },
      {
        task_id: "placeholder_easy_2",
        question: "5 - 3",
        expected_answer: "2",
        topic: request.topic,
        difficulty: "easy",
      },
      {
        task_id: "placeholder_easy_3",
        question: "3 + 1",
        expected_answer: "4",
        topic: request.topic,
        difficulty: "easy",
      },
      {
        task_id: "placeholder_easy_4",
        question: "6 - 2",
        expected_answer: "4",
        topic: request.topic,
        difficulty: "easy",
      },
    ],
    medium: [
      {
        task_id: "placeholder_medium_1",
        question: "5 × 3",
        expected_answer: "15",
        topic: request.topic,
        difficulty: "medium",
      },
      {
        task_id: "placeholder_medium_2",
        question: "12 ÷ 3",
        expected_answer: "4",
        topic: request.topic,
        difficulty: "medium",
      },
      {
        task_id: "placeholder_medium_3",
        question: "7 × 4",
        expected_answer: "28",
        topic: request.topic,
        difficulty: "medium",
      },
      {
        task_id: "placeholder_medium_4",
        question: "18 ÷ 2",
        expected_answer: "9",
        topic: request.topic,
        difficulty: "medium",
      },
    ],
    hard: [
      {
        task_id: "placeholder_hard_1",
        question: "15 × 12",
        expected_answer: "180",
        topic: request.topic,
        difficulty: "hard",
      },
      {
        task_id: "placeholder_hard_2",
        question: "144 ÷ 12",
        expected_answer: "12",
        topic: request.topic,
        difficulty: "hard",
      },
      {
        task_id: "placeholder_hard_3",
        question: "23 × 8",
        expected_answer: "184",
        topic: request.topic,
        difficulty: "hard",
      },
      {
        task_id: "placeholder_hard_4",
        question: "96 ÷ 8",
        expected_answer: "12",
        topic: request.topic,
        difficulty: "hard",
      },
    ],
  };

  return placeholders[request.difficulty].slice(0, request.count);
}

export async function analyseAnswer(
  taskId: string,
  strokes: Stroke[],
): Promise<AnalysisResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/assistant/analyse`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
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
  } catch (error) {
    console.error("Error analyzing answer:", error);

    // Placeholder logic until API is available
    const isCorrect = Math.random() > 0.5;
    return {
      has_issue: !isCorrect,
      message: isCorrect
        ? "Great work! That looks correct!"
        : "Try checking your work. Remember to show all your steps!",
      confidence: 0.8,
    };
  }
}
