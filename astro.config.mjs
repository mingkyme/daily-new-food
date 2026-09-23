// @ts-check
import sitemap from '@astrojs/sitemap';
import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://food.mingky.me',
  trailingSlash: 'always',
  integrations: [sitemap()],
});
