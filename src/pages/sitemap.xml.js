import { getCollection } from 'astro:content';

const escapeXml = (value) => value
  .replaceAll('&', '&amp;')
  .replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;')
  .replaceAll("'", '&apos;');

export async function GET({ site }) {
  const baseUrl = site ?? new URL('https://food.mingky.me');
  const posts = await getCollection('news', ({ data }) => !data.draft);
  const entries = [
    { url: new URL('/', baseUrl), lastmod: undefined },
    ...posts.map((post) => ({
      url: new URL(`/news/${post.id}/`, baseUrl),
      lastmod: post.data.updatedAt ?? post.data.publishedAt,
    })),
  ].sort((a, b) => a.url.href.localeCompare(b.url.href));

  const urls = entries.map(({ url, lastmod }) => {
    const modified = lastmod
      ? `\n    <lastmod>${lastmod.toISOString().slice(0, 10)}</lastmod>`
      : '';
    return `  <url>\n    <loc>${escapeXml(url.href)}</loc>${modified}\n  </url>`;
  }).join('\n');

  const body = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`;

  return new Response(body, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
    },
  });
}
