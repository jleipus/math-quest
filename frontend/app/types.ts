export type Point = { x: number; y: number };

export type Stroke = {
  points: Point[];
  timestamp_ms: number;
};

export type Difficulty = 'easy' | 'medium' | 'hard';

export type Task = {
  task_id: string;
  question: string;
  expected_answer: string;
  topic: string;
  difficulty: Difficulty;
};

export type Card = Task & {
  damage: number;
};

export type Player = {
  name: string;
  health: number;
  maxHealth: number;
  avatar: string;
};

export type AnalysisResult = {
  has_issue: boolean;
  message: string;
  suggestion?: string;
  confidence: number;
};
