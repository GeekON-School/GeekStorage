import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    outDir: 'static/dist',
    emptyOutDir: true,
    manifest: false,
    rollupOptions: {
      input: 'src/main.js',
      output: {
        entryFileNames: 'assets/main.js',
        chunkFileNames: 'assets/[name].js',
        assetFileNames: (assetInfo) => {
          if (assetInfo.name && assetInfo.name.endsWith('.css')) {
            return 'assets/main.css';
          }
          return 'assets/[name][extname]';
        }
      }
    }
  }
});
