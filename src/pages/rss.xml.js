import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';

export async function GET(context) {
  const posts = (await getCollection('news', ({ data }) => !data.draft))
    .sort((a, b) => b.data.publishedAt.valueOf() - a.data.publishedAt.valueOf());

  return rss({
    title: '오늘의 신상 식품',
    description: '편의점과 식품업계의 새로운 출시 소식을 매일 정리합니다.',
    site: context.site,
    items: posts.map((post) => ({
      title: post.data.title,
      description: post.data.description,
      pubDate: post.data.publishedAt,
      link: `news/${post.id}/`,
      categories: post.data.tags,
    })),
  });
}
