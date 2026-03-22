import { getIdToken } from "./firebase";
import type {
  FetchHandRequest,
  FetchHandResponse,
  RecordAnswerRequest,
  RecordAnswerResponse,
  HintRequest,
  HintResponse,
  UserModelResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export async function fetchHand(payload: FetchHandRequest): Promise<FetchHandResponse> {
  return post<FetchHandResponse>("/game/hand", payload);
}

export async function recordAnswer(payload: RecordAnswerRequest): Promise<RecordAnswerResponse> {
  return post<RecordAnswerResponse>("/game/answer", payload);
}

export async function requestHint(payload: HintRequest): Promise<HintResponse> {
  return post<HintResponse>("/game/hint", payload);
}

export async function fetchUserModel(): Promise<UserModelResponse> {
  return get<UserModelResponse>("/user_model");
}

export async function resetUserModel(): Promise<void> {
  await del("/user_model");
}

export async function fetchGrades(): Promise<string[]> {
  const data = await get<{ grades: string[] }>("/curriculum/grades");
  return data.grades;
}

async function authHeaders(): Promise<Record<string, string>> {
  const headers: Record<string, string> = {};
  const token = await getIdToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(await authHeaders()),
  };

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

async function del(path: string): Promise<void> {
  const headers = await authHeaders();
  const res = await fetch(`${API_BASE}${path}`, { method: "DELETE", headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `Request failed: ${res.status}`);
  }
}

async function get<T>(path: string): Promise<T> {
  const headers = await authHeaders();

  const res = await fetch(`${API_BASE}${path}`, { headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}
