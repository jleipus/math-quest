import type {
  HelpRequest,
  HelpResponse,
  CurriculumTopic,
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
  NextFloorRequest,
  NextFloorResponse,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export async function requestHelp({
  session_id,
  task_id,
  student_work,
}: HelpRequest): Promise<HelpResponse> {
  return post<HelpResponse>("/agent/help", { session_id, task_id, student_work });
}

/** Step 1: Create a session (no cards yet). */
export async function initGame({ topic }: InitGameRequest): Promise<InitGameResponse> {
  return post<InitGameResponse>("/game/init", { topic });
}

/** Step 2: Draw a hand of mixed-difficulty cards. */
export async function drawHand({ session_id }: DrawHandRequest): Promise<DrawHandResponse> {
  return post<DrawHandResponse>("/game/draw", { session_id });
}

export async function submitAnswer({
  session_id,
  task_id,
  answer,
}: AnswerRequest): Promise<AnswerResponse> {
  return post<AnswerResponse>("/game/answer", { session_id, task_id, answer });
}

export async function playCard({
  session_id,
  card_id,
}: PlayCardRequest): Promise<PlayCardResponse> {
  return post<PlayCardResponse>("/game/play_card", { session_id, card_id });
}

/** End turn: enemy attacks, then fresh hand is dealt. */
export async function endTurn({ session_id }: EndTurnRequest): Promise<EndTurnResponse> {
  return post<EndTurnResponse>("/game/end_turn", { session_id });
}

/** Advance to the next floor after defeating the current enemy. */
export async function nextFloor({ session_id }: NextFloorRequest): Promise<NextFloorResponse> {
  return post<NextFloorResponse>("/game/next_floor", { session_id });
}

export async function fetchTopics(): Promise<CurriculumTopic[]> {
  const data = await get<{ topics: CurriculumTopic[] }>("/curriculum/topics");
  return data.topics;
}

// Wrapper function for POST
async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
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
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Request failed: ${res.status}`);
  }
  return res.json();
}
