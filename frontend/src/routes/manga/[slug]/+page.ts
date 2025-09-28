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

    return {
      manga: finalManga,
      chapters: finalChapters
    };
  } catch (err) {
    console.error('Failed to load manga:', err);
    throw error(404, 'Manga not found');
  }
};