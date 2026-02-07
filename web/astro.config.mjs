import { defineConfig } from 'astro/config';

// https://docs.astro.build/reference/configuration-reference/
export default defineConfig({
  // Static build; API is served by Flask
  output: 'static',
  build: {
    assets: 'assets',
  },
});
