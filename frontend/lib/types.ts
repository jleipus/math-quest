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

// Curriculum

export type CurriculumTopic = {
  id: string;
  name: string;
  subtopics: string[];
  grade_level: string;
};

// Game

export type Difficulty = "easy" | "medium" | "hard";

export type CardType = "attack" | "heal" | "shield";

export type InitGameRequest = {
  topic: string;
};

export type InitGameResponse = {
  session_id: string;
  player_hp: number;
  enemy_hp: number;
  floor: number;
};

export type DrawHandRequest = {
  session_id: string;
};

export type Task = {
  task_id: string;
  question: string;
  topic: string;
  difficulty: Difficulty;
};

export type Card = {
  card_id: string;
  card_name: string;
  card_power: number;
  card_type: CardType;
  locked: boolean;
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
};

export const ENERGY_COST: Record<Difficulty, number> = {
  easy: 1,
  medium: 2,
  hard: 3,
};

export const MAX_ENERGY = 3;

export type AnswerRequest = {
  session_id: string;
  task_id: string;
  answer: string;
};

export type AnswerResponse = {
  correct: boolean;
  card_id: string;
  card_unlocked: boolean;
  player_hp: number;
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

export type AgentMessage = {
  guiding_question: string;
};

export type NextFloorRequest = {
  session_id: string;
};

export type NextFloorResponse = {
  floor: number;
  enemy_hp: number;
  enemy_max_hp: number;
  enemy_next_damage: number;
};
