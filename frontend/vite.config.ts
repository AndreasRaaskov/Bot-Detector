import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
    proxy: {
      // Proxy API calls during development to the backend running on port 8000
      // This avoids CORS issues and lets the frontend call relative paths like `/analyze`
      "/analyze": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/config": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/health": {
        target: "http://localhost:8000",
        changeOrigin: true,
      }
    },
  },
  build: {
    // Ensure the build output goes to dist/ directory
    outDir: "dist",
    // Generate source maps for debugging in production
    sourcemap: mode === "development",
    // Clean the output directory before building
    emptyOutDir: true,
  },
  base: "/",
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
