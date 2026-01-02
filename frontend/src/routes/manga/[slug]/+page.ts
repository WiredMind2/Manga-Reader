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

    return {
      manga,
      chapters
    };
  } catch (err) {
    console.error('Failed to load manga:', err);
    // Re-throw 404s
    if ((err as any)?.status === 404) {
      throw error(404, 'Manga not found');
    }
    throw err;
  }
};