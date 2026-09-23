import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  envDir: "../..",

  plugins: [react(), tailwindcss()],

  server: {
    host: "0.0.0.0",
    port: 5173,
  },

  preview: {
    host: "0.0.0.0",
    port: 4173,
  },

  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
  },
});
