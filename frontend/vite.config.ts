import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    host: true,
  },
  preview: {
    port: 4173,
  },
  build: {
    rollupOptions: {
      output: {
        // Split heavy, independently-cacheable vendor libs out of the main bundle.
        manualChunks: {
          react: ["react", "react-dom", "react-router-dom"],
          charts: ["recharts"],
          markdown: ["react-markdown", "remark-gfm"],
          query: ["@tanstack/react-query", "@tanstack/react-table"],
        },
      },
    },
  },
});
