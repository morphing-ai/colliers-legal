// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    hmr: {
      // Enable HMR for development
      port: 3000,
      host: 'localhost'
    },
    watch: {
      // Use polling for better compatibility with Docker
      usePolling: true,
      interval: 1000
    },
    allowedHosts: [
      'legal-colliers.dev.morphing.ai',
      'localhost',
      '127.0.0.1',
      '.morphing.ai'  // Allow all subdomains
    ]
  },
  preview: {
    port: 3000,
    host: '0.0.0.0',
    allowedHosts: [
      'legal-colliers.dev.morphing.ai',
      'localhost',
      '127.0.0.1',
      '.morphing.ai'
    ]
  }
});