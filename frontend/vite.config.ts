import path from "node:path";
import { fileURLToPath, URL } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig, searchForWorkspaceRoot } from "vite";

const projectRoot = fileURLToPath(new URL(".", import.meta.url));
const workspaceRoot = path.resolve(projectRoot, "..");

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      "@repo-assets": path.resolve(projectRoot, "../assets"),
    },
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    fs: {
      allow: [searchForWorkspaceRoot(process.cwd()), workspaceRoot],
    },
  },
  preview: {
    host: "0.0.0.0",
    port: 4173,
  },
});
