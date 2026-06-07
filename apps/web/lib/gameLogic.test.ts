import { describe, it, expect } from "vitest";
import { checkAnswer } from "./gameLogic";
import type { Task } from "./types";

function task(overrides: Partial<Task> = {}): Task {
  return {
    task_id: "t1",
    question: "q",
    grade: "g",
    topic: "topic",
    difficulty: "easy",
    expected_answer: "0",
    answer_type: "number",
    accepted_answers: [],
    ...overrides,
  };
}

describe("checkAnswer — numeric", () => {
  it("accepts an exact integer match", () => {
    expect(checkAnswer("4", task({ expected_answer: "4" }))).toBe(true);
  });

  it("ignores surrounding whitespace", () => {
    expect(checkAnswer("  4 ", task({ expected_answer: "4" }))).toBe(true);
  });

  it("treats a comma as a decimal separator", () => {
    expect(checkAnswer("3,5", task({ expected_answer: "3.5" }))).toBe(true);
  });

  it("compares floats within tolerance", () => {
    expect(checkAnswer("0.1000001", task({ expected_answer: "0.1" }))).toBe(true);
  });

  it("rejects a wrong number", () => {
    expect(checkAnswer("5", task({ expected_answer: "4" }))).toBe(false);
  });
});

describe("checkAnswer — fraction", () => {
  it("accepts an equivalent unreduced fraction", () => {
    expect(checkAnswer("2/4", task({ answer_type: "fraction", expected_answer: "1/2" }))).toBe(true);
  });

  it("rejects a non-equivalent fraction", () => {
    expect(checkAnswer("3/4", task({ answer_type: "fraction", expected_answer: "1/2" }))).toBe(false);
  });
});

describe("checkAnswer — text", () => {
  const shape = (overrides: Partial<Task> = {}) =>
    task({ answer_type: "text", expected_answer: "triangel", ...overrides });

  it("matches the expected answer case-insensitively", () => {
    expect(checkAnswer("Triangel", shape())).toBe(true);
  });

  it("ignores trailing punctuation and extra whitespace", () => {
    expect(checkAnswer("  triangel. ", shape())).toBe(true);
  });

  it("collapses internal whitespace", () => {
    expect(checkAnswer("röd  triangel", shape({ expected_answer: "röd triangel" }))).toBe(true);
  });

  it("accepts a provided variant", () => {
    expect(checkAnswer("triangeln", shape({ accepted_answers: ["triangeln"] }))).toBe(true);
  });

  it("rejects a wrong word", () => {
    expect(checkAnswer("kvadrat", shape())).toBe(false);
  });

  it("keeps Swedish letters significant (no diacritic folding)", () => {
    expect(checkAnswer("apple", shape({ expected_answer: "äpple" }))).toBe(false);
  });

  it("does not numerically match a text task", () => {
    // "två" and "2" are not equal under text comparison
    expect(checkAnswer("2", shape({ expected_answer: "två" }))).toBe(false);
  });
});
