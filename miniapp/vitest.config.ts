import { defineConfig, mergeConfig } from 'vitest/config';
import viteConfig from './vite.config';

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      globals: true,
      setupFiles: ['./src/test/setup.ts'],
      env: {
        VITE_API_BASE_URL: 'http://localhost:8000',
      },
      include: ['src/**/*.{test,spec}.{ts,tsx}'],
      coverage: {
        provider: 'v8',
        thresholds: {
          'src/entities/**': { lines: 70 },
          'src/features/**': { lines: 70 },
          'src/shared/lib/**': { lines: 80 },
          'src/shared/store/**': { lines: 80 },
        },
      },
    },
  }),
);
