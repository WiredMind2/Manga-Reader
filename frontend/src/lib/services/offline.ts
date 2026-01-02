import { openDB, type DBSchema } from 'idb';
import { browser } from '$app/environment';

interface MangaDB extends DBSchema {
  mangas: {
    key: string;
    value: any;
  };
  chapters: {
    key: number;
    value: any;
    indexes: { 'by-manga': number };
  };
  pages: {
    key: string; // format: chapterId_pageIndex
    value: Blob;
  };
}

const DB_NAME = 'manga-reader-offline';
const DB_VERSION = 1;

export class OfflineStorage {
  private dbPromise;

  constructor() {
    if (browser) {
      this.dbPromise = openDB<MangaDB>(DB_NAME, DB_VERSION, {
        upgrade(db) {
          if (!db.objectStoreNames.contains('mangas')) {
            db.createObjectStore('mangas', { keyPath: 'slug' });
          }
          if (!db.objectStoreNames.contains('chapters')) {
            const chapterStore = db.createObjectStore('chapters', { keyPath: 'id' });
            chapterStore.createIndex('by-manga', 'manga_id');
          }
          if (!db.objectStoreNames.contains('pages')) {
            db.createObjectStore('pages');
          }
        },
      });
    }
  }

  async saveManga(manga: any) {
    if (!this.dbPromise) return;
    const db = await this.dbPromise;
    await db.put('mangas', manga);
  }

  async getManga(slug: string) {
    if (!this.dbPromise) return null;
    const db = await this.dbPromise;
    return db.get('mangas', slug);
  }

  async getAllMangas() {
    if (!this.dbPromise) return [];
    const db = await this.dbPromise;
    return db.getAll('mangas');
  }

  async saveChapter(chapter: any) {
    if (!this.dbPromise) return;
    const db = await this.dbPromise;
    await db.put('chapters', chapter);
  }

  async getChapter(id: number) {
    if (!this.dbPromise) return null;
    const db = await this.dbPromise;
    return db.get('chapters', id);
  }

  async getChaptersForManga(mangaId: number) {
    if (!this.dbPromise) return [];
    const db = await this.dbPromise;
    return db.getAllFromIndex('chapters', 'by-manga', mangaId);
  }

  async savePage(chapterId: number, pageIndex: number, blob: Blob) {
    if (!this.dbPromise) return;
    const db = await this.dbPromise;
    await db.put('pages', blob, `${chapterId}_${pageIndex}`);
  }

  async getPage(chapterId: number, pageIndex: number) {
    if (!this.dbPromise) return null;
    const db = await this.dbPromise;
    return db.get('pages', `${chapterId}_${pageIndex}`);
  }

  async isChapterDownloaded(chapterId: number): Promise<boolean> {
    if (!this.dbPromise) return false;
    const db = await this.dbPromise;
    const chapter = await db.get('chapters', chapterId);
    return !!chapter?.downloaded;
  }
  
  async deleteChapter(chapterId: number) {
      if (!this.dbPromise) return;
      const db = await this.dbPromise;
      const tx = db.transaction(['chapters', 'pages'], 'readwrite');
      await tx.objectStore('chapters').delete(chapterId);
      
      let cursor = await tx.objectStore('pages').openCursor(IDBKeyRange.bound(`${chapterId}_0`, `${chapterId}_\uffff`));
      while (cursor) {
          await cursor.delete();
          cursor = await cursor.continue();
      }
      await tx.done;
  }
}

export const offlineStorage = new OfflineStorage();
