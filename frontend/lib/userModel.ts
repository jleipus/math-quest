import type { DifficultyRecord, TopicRecord } from "./types";

export type LocalUserModel = {
  topics: Record<string, Record<string, DifficultyRecord>>;
};

const STORAGE_KEY = "mathquest_user_model";

export function loadLocalUserModel(): LocalUserModel {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as LocalUserModel;
  } catch {
    // ignore
  }
  return { topics: {} };
}

export function saveLocalUserModel(model: LocalUserModel): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(model));
  } catch {
    // ignore
  }
}

export function clearLocalUserModel(): void {
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
}

function getOrCreateRecord(
  model: LocalUserModel,
  topic: string,
  difficulty: string,
): { model: LocalUserModel; record: DifficultyRecord } {
  const topics = { ...model.topics };
  if (!topics[topic]) topics[topic] = {};
  const diffs = { ...topics[topic] };
  if (!diffs[difficulty]) {
    diffs[difficulty] = { topic, difficulty, attempts: 0, hints: 0, correct: 0 };
  }
  const record = { ...diffs[difficulty] };
  diffs[difficulty] = record;
  topics[topic] = diffs;
  return { model: { topics }, record };
}

export function recordAttemptLocal(
  model: LocalUserModel,
  topic: string,
  difficulty: string,
  correct: boolean,
): LocalUserModel {
  const { model: next, record } = getOrCreateRecord(model, topic, difficulty);
  record.attempts += 1;
  if (correct) record.correct += 1;
  return next;
}

export function recordHintLocal(
  model: LocalUserModel,
  topic: string,
  difficulty: string,
): LocalUserModel {
  const { model: next, record } = getOrCreateRecord(model, topic, difficulty);
  record.hints += 1;
  return next;
}

export function toTopicRecords(model: LocalUserModel): TopicRecord[] {
  return Object.entries(model.topics).map(([topic, diffs]) => ({
    topic,
    records: diffs,
  }));
}
