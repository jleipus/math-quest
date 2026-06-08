import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Monorepo: trace from the repo root so the build resolves workspace
  // dependencies correctly (and to disambiguate the workspace root).
  outputFileTracingRoot: path.join(__dirname, "../../"),
};

export default nextConfig;
