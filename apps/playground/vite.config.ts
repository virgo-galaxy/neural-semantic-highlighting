import { fileURLToPath, URL } from "node:url";

import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

import { localSemanticProviderPlugin } from "./vite/local-semantic-provider.ts";

export default defineConfig({
  plugins: [vue(), localSemanticProviderPlugin()],

  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },

  server: {
    host: "127.0.0.1",
    port: 3000,
    strictPort: true,
    open: true,
  },
});
