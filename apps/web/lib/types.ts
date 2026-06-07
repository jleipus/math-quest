/**
 * Frontend API types.
 *
 * These are aliases over the backend's OpenAPI schema (generated into
 * ./api-schema.ts), which is the single source of truth. After changing the
 * Pydantic models in backend/models, regenerate with `npm run gen:api-types`
 * from the repo root.
 */
import type { components } from "./api-schema";

type Schemas = components["schemas"];

export type Point = Schemas["Point"];
export type Stroke = Schemas["Stroke"];
export type Task = Schemas["Task"];
export type Card = Schemas["Card"];
export type FetchHandRequest = Schemas["FetchHandRequest"];
export type FetchHandResponse = Schemas["FetchHandResponse"];
export type RecordAnswerRequest = Schemas["RecordAnswerRequest"];
export type RecordAnswerResponse = Schemas["RecordAnswerResponse"];
export type HintRequest = Schemas["HintRequest"];
export type HintResponse = Schemas["HintResponse"];
export type GradesResponse = Schemas["GradesResponse"];
export type DifficultyRecord = Schemas["DifficultyRecord"];
export type TopicRecord = Schemas["TopicRecord"];
export type UserModelResponse = Schemas["UserModelResponse"];

// Inline unions on the Card schema (not standalone OpenAPI components), derived
// so they still track the backend definition.
export type CardType = Schemas["Card"]["card_type"];
export type AttackSubtype = NonNullable<Schemas["Card"]["attack_subtype"]>;

// Frontend-only: the backend types difficulty as a free-form string, but the
// UI works with a fixed set of levels.
export type Difficulty = "easy" | "medium" | "hard";
