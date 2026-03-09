import type {
  StartSessionRequest,
  StartSessionResponse,
  FetchHandRequest,
  FetchHandResponse,
  RecordAnswerRequest,
  RecordAnswerResponse,
  HintRequest,
  HintResponse,
  UserModelResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";

export async function startSession(payload: StartSessionRequest): Promise<StartSessionResponse> {
  return post<StartSessionResponse>("/game/start", payload);
}

export async function fetchHand(payload: FetchHandRequest): Promise<FetchHandResponse> {
  return post<FetchHandResponse>("/game/hand", payload);
}

export async function recordAnswer(payload: RecordAnswerRequest): Promise<RecordAnswerResponse> {
  return post<RecordAnswerResponse>("/game/answer", payload);
}

export async function requestHint(payload: HintRequest): Promise<HintResponse> {
  return post<HintResponse>("/game/hint", payload);
}

export async function fetchUserModel(session_id: string): Promise<UserModelResponse> {
  return get<UserModelResponse>(`/user_model/${session_id}`);
}

export async function fetchGrades(): Promise<string[]> {
  const data = await get<{ grades: string[] }>("/curriculum/grades");
  return data.grades;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (API_KEY) headers["X-API-Key"] = API_KEY;

  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

async function get<T>(path: string): Promise<T> {
  const headers: Record<string, string> = {};
  if (API_KEY) headers["X-API-Key"] = API_KEY;

  const res = await fetch(`${API_BASE}${path}`, { headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}
