import type { PageLoad } from './$types';
import { apiClient } from '$lib/api/client';
import { error } from '@sveltejs/kit';

export const load: PageLoad = async ({ params }) => {
  try {
    const [manga, chapters] = await Promise.all([
      apiClient.getMangaBySlug(params.slug),
      apiClient.getMangaChapters(parseInt(params.slug) || 0).catch(() => [])
    ]);

    // If getMangaBySlug fails, try by ID
    let finalManga = manga;
    let finalChapters = chapters;

    if (!manga && params.slug.match(/^\d+$/)) {
      try {
        finalManga = await apiClient.getMangaById(parseInt(params.slug));
        finalChapters = await apiClient.getMangaChapters(finalManga.id);
      } catch {
        throw error(404, 'Manga not found');
      }
    }

    if (!finalManga) {
      throw error(404, 'Manga not found');
    }

    const chapterId = parseInt(params.chapter);
    const chapter = finalChapters.find((c: any) => c.id === chapterId);
    
    if (!chapter) {
      throw error(404, 'Chapter not found');
    }

    const pages = await apiClient.getChapterPages(finalManga.id, chapterId);

    return {
      manga: finalManga,
      chapters: finalChapters,
      chapter,
      pages
    };
  } catch (err: any) {
    console.error('Failed to load chapter:', err);
    if (err.status === 404) {
      throw err;
    }
    throw error(500, 'Failed to load chapter');
  }
};