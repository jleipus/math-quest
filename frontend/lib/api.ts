import type {
  HelpRequest,
  HelpResponse,
  InitGameRequest,
  InitGameResponse,
  DrawHandRequest,
  DrawHandResponse,
  EndTurnRequest,
  EndTurnResponse,
  AnswerRequest,
  AnswerResponse,
  PlayCardRequest,
  PlayCardResponse,
  UserModelResponse,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

// Optional shared API key — set NEXT_PUBLIC_API_KEY in your environment to enable.
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";

export async function requestHelp({
  session_id,
  x_session_token,
  task_id,
  student_work,
  canvas_width,
  canvas_height,
  previous_questions,
}: HelpRequest): Promise<HelpResponse> {
  return post<HelpResponse>("/agent/help", {
    session_id,
    x_session_token,
    task_id,
    student_work,
    canvas_width,
    canvas_height,
    previous_questions,
  });
}

export async function initGame({ grade }: InitGameRequest): Promise<InitGameResponse> {
  return post<InitGameResponse>("/game/init", { grade });
}

export async function drawHand({
  session_id,
  x_session_token,
}: DrawHandRequest): Promise<DrawHandResponse> {
  return post<DrawHandResponse>("/game/draw", { session_id, x_session_token });
}

export async function submitAnswer({
  session_id,
  x_session_token,
  task_id,
  answer,
}: AnswerRequest): Promise<AnswerResponse> {
  return post<AnswerResponse>("/game/answer", { session_id, x_session_token, task_id, answer });
}

export async function playCard({
  session_id,
  x_session_token,
  card_id,
}: PlayCardRequest): Promise<PlayCardResponse> {
  return post<PlayCardResponse>("/game/play_card", { session_id, x_session_token, card_id });
}

export async function endTurn({
  session_id,
  x_session_token,
}: EndTurnRequest): Promise<EndTurnResponse> {
  return post<EndTurnResponse>("/game/end_turn", { session_id, x_session_token });
}

export async function fetchUserModel(session_id: string): Promise<UserModelResponse> {
  return get<UserModelResponse>(`/user_model/${session_id}`);
}

export async function fetchGrades(): Promise<string[]> {
  const data = await get<{ grades: string[] }>("/curriculum/grades");
  return data.grades;
}

// Wrapper function for POST
async function post<T>(path: string, body: unknown): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (API_KEY) headers["X-API-Key"] = API_KEY;

  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Request failed: ${res.status}`);
  }
  return res.json();
}

// Wrapper function for GET
async function get<T>(path: string): Promise<T> {
  const headers: Record<string, string> = {};
  if (API_KEY) headers["X-API-Key"] = API_KEY;

  const res = await fetch(`${BASE}${path}`, { headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Request failed: ${res.status}`);
  }
  return res.json();
}
