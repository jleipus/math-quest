export type Point = {
  x: number;
  y: number;
};

export type Stroke = {
  points: Point[];
  timestamp_ms: number;
};

export type Difficulty = "easy" | "medium" | "hard";
export type CardType = "attack" | "heal" | "shield";
export type AttackSubtype = "magic" | "bow" | "sword" | "axe";

export type Task = {
  task_id: string;
  question: string;
  grade: string;
  topic: string;
  difficulty: Difficulty;
  expected_answer: string;
};

export type Card = {
  card_id: string;
  card_name: string;
  card_power: number;
  card_type: CardType;
  attack_subtype: AttackSubtype | null;
  energy_cost: number;
  task: Task;
};

export type FetchHandRequest = {
  grade: string;
};

export type FetchHandResponse = {
  hand: Card[];
};

export type RecordAnswerRequest = {
  topic: string;
  difficulty: string;
  correct: boolean;
};

export type RecordAnswerResponse = {
  ok: boolean;
};

export type HintRequest = {
  grade: string;
  topic: string;
  difficulty: string;
  question: string;
  student_work?: Stroke[];
  canvas_width?: number;
  canvas_height?: number;
  previous_hints?: string[];
};

export type HintResponse = {
  guiding_question: string;
};

export type GradesResponse = {
  grades: string[];
};

export type DifficultyRecord = {
  topic: string;
  difficulty: string;
  attempts: number;
  hints: number;
  correct: number;
};

export type TopicRecord = {
  topic: string;
  records: Record<string, DifficultyRecord>;
};

export type UserModelResponse = {
  topics: TopicRecord[];
};
