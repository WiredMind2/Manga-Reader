import { describe, it, expect } from 'vitest';

// Simple utility functions to test API URL generation
function getPageImageUrl(
  mangaId: number, 
  chapterId: number, 
  pageId: number, 
  options: {
    width?: number
    height?: number
    quality?: number
    thumbnail?: boolean
  } = {}
): string {
  const baseURL = 'http://localhost:8000/api';
  const params = new URLSearchParams();
  
  Object.entries(options).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      params.append(key, value.toString());
    }
  });

  const query = params.toString();
  const endpoint = `/images/${mangaId}/${chapterId}/${pageId}`;
  
  return `${baseURL}${endpoint}${query ? `?${query}` : ''}`;
}

function getCoverImageUrl(
  mangaId: number,
  options: {
    width?: number
    height?: number
    quality?: number
  } = {}
): string {
  const baseURL = 'http://localhost:8000/api';
  const params = new URLSearchParams();
  
  Object.entries(options).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      params.append(key, value.toString());
    }
  });

  const query = params.toString();
  const endpoint = `/covers/${mangaId}`;
  
  return `${baseURL}${endpoint}${query ? `?${query}` : ''}`;
}

describe('API URL Generation', () => {
  describe('getPageImageUrl', () => {
    it('generates correct URL without options', () => {
      const url = getPageImageUrl(1, 2, 3);
      expect(url).toBe('http://localhost:8000/api/images/1/2/3');
    });

    it('generates correct URL with width and height', () => {
      const url = getPageImageUrl(1, 2, 3, { width: 800, height: 600 });
      expect(url).toBe('http://localhost:8000/api/images/1/2/3?width=800&height=600');
    });

    it('generates correct URL with quality option', () => {
      const url = getPageImageUrl(1, 2, 3, { quality: 85 });
      expect(url).toBe('http://localhost:8000/api/images/1/2/3?quality=85');
    });

    it('generates correct URL with thumbnail option', () => {
      const url = getPageImageUrl(1, 2, 3, { thumbnail: true });
      expect(url).toBe('http://localhost:8000/api/images/1/2/3?thumbnail=true');
    });

    it('generates correct URL with all options', () => {
      const url = getPageImageUrl(1, 2, 3, { 
        width: 800, 
        height: 600, 
        quality: 85, 
        thumbnail: false 
      });
      expect(url).toBe('http://localhost:8000/api/images/1/2/3?width=800&height=600&quality=85&thumbnail=false');
    });
  });

  describe('getCoverImageUrl', () => {
    it('generates correct URL without options', () => {
      const url = getCoverImageUrl(1);
      expect(url).toBe('http://localhost:8000/api/covers/1');
    });

    it('generates correct URL with width and height', () => {
      const url = getCoverImageUrl(1, { width: 400, height: 600 });
      expect(url).toBe('http://localhost:8000/api/covers/1?width=400&height=600');
    });

    it('generates correct URL with quality option', () => {
      const url = getCoverImageUrl(1, { quality: 90 });
      expect(url).toBe('http://localhost:8000/api/covers/1?quality=90');
    });
  });
});