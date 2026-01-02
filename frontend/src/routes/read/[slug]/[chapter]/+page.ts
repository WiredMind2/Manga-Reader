import type { PageLoad } from './$types';
import { apiClient } from '$lib/api/client';
import { error } from '@sveltejs/kit';

export const load: PageLoad = async ({ params }) => {
  try {
    let manga;
    
    // Try to fetch by slug first
    try {
      manga = await apiClient.getMangaBySlug(params.slug);
    } catch (e) {
      // If slug lookup fails and params.slug is a number, try by ID
      if (params.slug.match(/^\d+$/)) {
        try {
          manga = await apiClient.getMangaById(parseInt(params.slug));
        } catch {
          throw error(404, 'Manga not found');
        }
      } else {
        throw error(404, 'Manga not found');
      }
    }

    // Fetch chapters using the manga ID
    const chapters = await apiClient.getMangaChapters(manga.id).catch(() => []);

    const chapterId = parseInt(params.chapter);
    const chapter = chapters.find((c: any) => c.id === chapterId);
    
    if (!chapter) {
      throw error(404, 'Chapter not found');
    }

    const pages = await apiClient.getChapterPages(manga.id, chapterId);

    return {
      manga,
      chapters,
      chapter,
      pages
    };
  } catch (err: any) {
    console.error('Failed to load chapter:', err);
    if ((err as any)?.status === 404 || err?.body?.message === 'Not Found') {
      throw error(404, 'Chapter not found');
    }
    throw err;
  }
};