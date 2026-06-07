import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // gameLogic is pure TS (no DOM), so the node environment is enough.
    environment: "node",
    include: ["lib/**/*.test.ts"],
  },
});
