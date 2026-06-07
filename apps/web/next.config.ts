import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Monorepo: trace from the repo root so the standalone bundle resolves
  // workspace dependencies correctly (and to disambiguate the workspace root).
  outputFileTracingRoot: path.join(__dirname, "../../"),
};

export default nextConfig;
