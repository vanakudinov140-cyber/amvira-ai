import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

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
    proxy: {
      "/health": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/analytics": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/messages": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/scheduler": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/retention": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/debug": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "^/test/": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
  },
  preview: {
    port: 8080,
    host: true,
    proxy: {
      "/health": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/analytics": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/messages": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/scheduler": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/retention": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/debug": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "^/test/": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
  },
});
