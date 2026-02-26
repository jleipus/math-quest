// Assistant

export type Point = {
  x: number;
  y: number;
};

export type Stroke = {
  points: Point[];
  timestamp_ms: number;
};

export type HelpRequest = {
  session_id: string;
  task_id: string;
  student_work?: Stroke[];
};

export type HelpResponse = {
  guiding_question: string;
  context_used: string;
};

// Game

export type Difficulty = "easy" | "medium" | "hard";

export type CardType = "attack" | "heal" | "shield";

export type InitGameRequest = {
  grade: string;
};

export type InitGameResponse = {
  session_id: string;
  player_hp: number;
  enemy_hp: number;
  max_energy: number;
  floor: number;
};

export type DrawHandRequest = {
  session_id: string;
};

export type Task = {
  task_id: string;
  question: string;
  grade: string;
  topic: string;
  difficulty: Difficulty;
};

export type Card = {
  card_id: string;
  card_name: string;
  card_power: number;
  card_type: CardType;
  energy_cost: number;
  task: Task;
};

export type DrawHandResponse = {
  hand: Card[];
  enemy_next_damage: number;
};

export type EndTurnRequest = {
  session_id: string;
};

export type EndTurnResponse = {
  player_hp: number;
  enemy_damage: number;
  shield_absorbed: number;
  hand: Card[];
  enemy_next_damage: number;
  enemy_hp: number;
  enemy_max_hp: number;
};

export type AnswerRequest = {
  session_id: string;
  task_id: string;
  answer: string;
};

export type AnswerResponse = {
  correct: boolean;
  card_id: string;
  message: string;
};

export type PlayCardRequest = {
  session_id: string;
  card_id: string;
};

export type PlayCardResponse = {
  enemy_hp: number;
  player_hp: number;
  effect_value: number;
  card_type: CardType;
  enemy_defeated: boolean;
};

// User model

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
  session_id: string;
  topics: TopicRecord[];
};
