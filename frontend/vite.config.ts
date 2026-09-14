import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "./",
  build: {
    outDir: "dist",
  },
  server: {
    watch: {
      // Electron et les assets lourds ne concernent pas le dev web :
      // les exclure évite les crashs EBUSY sous Windows.
      ignored: ["**/electron/**", "**/dist/**", "**/*.png"],
    },
  },
});
