import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import MangaGrid from './MangaGrid.svelte';
import type { Manga } from '../api/types';

// Mock modules first
vi.mock('$app/navigation', () => ({
	goto: vi.fn()
}));

vi.mock('../api/client', () => ({
	apiClient: {
		getCoverImageUrl: vi.fn((id: number, options?: any) => 
			`https://api.example.com/covers/${id}?width=${options?.width}&height=${options?.height}`
		)
	}
}));

// Import after mocking
import { goto } from '$app/navigation';
import { apiClient } from '../api/client';

describe('MangaGrid', () => {
	let mockManga: Manga[];
	let user: ReturnType<typeof userEvent.setup>;

	beforeEach(() => {
		vi.clearAllMocks();
		user = userEvent.setup();
		
		mockManga = [
			{
				id: 1,
				title: 'One Piece',
				slug: 'one-piece',
				author: 'Eiichiro Oda',
				description: 'A story about pirates and adventure on the high seas.',
				status: 'ongoing',
				total_chapters: 1000,
				cover_image: '/covers/one-piece.jpg'
			},
			{
				id: 2,
				title: 'Naruto',
				slug: 'naruto',
				author: 'Masashi Kishimoto',
				description: 'A young ninja seeks recognition from his peers.',
				status: 'completed' as const,
				total_chapters: 700,
				cover_image: '/covers/naruto.jpg',
				created_at: '2023-01-02T00:00:00Z'
			},
			{
				id: 3,
				title: 'Very Long Title That Should Be Truncated Because It Exceeds The Character Limit',
				slug: 'long-title',
				author: 'Test Author With Very Long Name That Should Also Be Truncated',
				description: 'A very long description that should be truncated when displayed in the manga grid to ensure proper layout and readability.',
				status: 'hiatus' as const,
				total_chapters: 50,
				cover_image: undefined,
				created_at: '2023-01-03T00:00:00Z'
			}
		];
	});

	it('renders empty grid when no manga provided', () => {
		render(MangaGrid, { manga: [] });
		
		const grid = document.querySelector('.grid');
		expect(grid).toBeInTheDocument();
		expect(grid?.children.length).toBe(0);
	});

	it('renders manga cards for provided manga', () => {
		render(MangaGrid, { manga: mockManga });
		
		expect(screen.getByText('One Piece')).toBeInTheDocument();
		expect(screen.getByText('Naruto')).toBeInTheDocument();
		expect(screen.getByText('Very Long Title That Should Be Truncated Becau...')).toBeInTheDocument();
	});

	it('displays manga information correctly', () => {
		render(MangaGrid, { manga: [mockManga[0]] });
		
		expect(screen.getByText('One Piece')).toBeInTheDocument();
		expect(screen.getByText('by Eiichiro Oda')).toBeInTheDocument();
		expect(screen.getByText('A story about pirates and adventure on the high seas.')).toBeInTheDocument();
		expect(screen.getByText('1000 ch')).toBeInTheDocument();
		expect(screen.getByText('ongoing')).toBeInTheDocument();
	});

	it('generates correct cover image URLs', () => {
		render(MangaGrid, { manga: [mockManga[0]] });
		
		const coverImage = screen.getByAltText('One Piece') as HTMLImageElement;
		expect(coverImage.src).toBe('https://api.example.com/covers/1?width=300&height=400');
		expect(apiClient.getCoverImageUrl).toHaveBeenCalledWith(1, { width: 300, height: 400 });
	});

	it('applies correct status colors', () => {
		render(MangaGrid, { manga: mockManga });
		
		const ongoingBadge = screen.getByText('ongoing');
		expect(ongoingBadge).toHaveClass('bg-green-100', 'text-green-800');
		
		const completedBadge = screen.getByText('completed');
		expect(completedBadge).toHaveClass('bg-blue-100', 'text-blue-800');
		
		const hiatusBadge = screen.getByText('hiatus');
		expect(hiatusBadge).toHaveClass('bg-yellow-100', 'text-yellow-800');
	});

	it('handles manga click navigation', async () => {
		render(MangaGrid, { manga: [mockManga[0]] });
		
		const mangaCard = screen.getByRole('button', { name: /one piece/i });
		await user.click(mangaCard);
		
		expect(goto).toHaveBeenCalledWith('/manga/one-piece');
	});

	it('handles keyboard navigation', async () => {
		render(MangaGrid, { manga: [mockManga[0]] });
		
		const mangaCard = screen.getByRole('button');
		mangaCard.focus();
		await user.keyboard('{Enter}');
		
		expect(goto).toHaveBeenCalledWith('/manga/one-piece');
	});

	it('handles read button click', async () => {
		render(MangaGrid, { manga: [mockManga[0]] });
		
		const readButton = screen.getByText('Read Now');
		await user.click(readButton);
		
		expect(goto).toHaveBeenCalledWith('/manga/one-piece');
	});

	it('stops propagation on read button click', async () => {
		render(MangaGrid, { manga: [mockManga[0]] });
		
		const readButton = screen.getByText('Read Now');
		const clickEvent = new MouseEvent('click', { bubbles: true });
		const stopPropagationSpy = vi.spyOn(clickEvent, 'stopPropagation');
		
		await fireEvent(readButton, clickEvent);
		
		expect(stopPropagationSpy).toHaveBeenCalled();
	});

	it('truncates long titles correctly', () => {
		render(MangaGrid, { manga: [mockManga[2]] });
		
		const title = screen.getByText(/Very Long Title That Should Be Truncated/);
		expect(title.textContent).toBe('Very Long Title That Should Be Truncated Becau...');
	});

	it('truncates long author names correctly', () => {
		render(MangaGrid, { manga: [mockManga[2]] });
		
		const author = screen.getByText(/by Test Author With Very Long/);
		expect(author.textContent).toBe('by Test Author With Very Long N...');
	});

	it('truncates long descriptions correctly', () => {
		render(MangaGrid, { manga: [mockManga[2]] });
		
		const description = screen.getByText(/A very long description that should be truncated when displayed/);
		expect(description.textContent?.length).toBeLessThanOrEqual(83); // 80 chars + "..."
	});

	it('handles missing optional fields', () => {
		const minimalManga: Manga = {
			id: 4,
			title: 'Minimal Manga',
			slug: 'minimal-manga',
			total_chapters: 10
		};
		
		render(MangaGrid, { manga: [minimalManga] });
		
		expect(screen.getByText('Minimal Manga')).toBeInTheDocument();
		expect(screen.getByText('10 ch')).toBeInTheDocument();
		expect(screen.queryByText(/by /)).not.toBeInTheDocument();
	});

	it('shows fallback placeholder on image error', async () => {
		render(MangaGrid, { manga: [mockManga[0]] });
		
		const coverImage = screen.getByAltText('One Piece');
		
		// Simulate image load error
		await fireEvent.error(coverImage);
		
		// Image should be hidden
		expect(coverImage).toHaveStyle({ display: 'none' });
		
		// Placeholder should be visible
		const placeholder = screen.getByText('No Cover');
		expect(placeholder).toBeInTheDocument();
	});

	it('has proper accessibility attributes', () => {
		render(MangaGrid, { manga: [mockManga[0]] });
		
		const mangaCard = screen.getByRole('button');
		expect(mangaCard).toHaveAttribute('tabindex', '0');
		
		const coverImage = screen.getByAltText('One Piece');
		expect(coverImage).toHaveAttribute('alt', 'One Piece');
		expect(coverImage).toHaveAttribute('loading', 'lazy');
	});

	it('applies hover effects through CSS classes', () => {
		render(MangaGrid, { manga: [mockManga[0]] });
		
		const mangaCard = document.querySelector('.group');
		expect(mangaCard).toHaveClass('hover:shadow-lg', 'transition-shadow');
		
		const coverImage = screen.getByAltText('One Piece');
		expect(coverImage).toHaveClass('group-hover:scale-105', 'transition-transform');
		
		const title = screen.getByText('One Piece');
		expect(title).toHaveClass('group-hover:text-primary');
	});

	it('handles different status values correctly', () => {
		const statusManga: Manga[] = [
			{ ...mockManga[0], status: 'cancelled' },
			{ ...mockManga[0], status: 'unknown' },
			{ ...mockManga[0], status: undefined }
		];
		
		render(MangaGrid, { manga: statusManga });
		
		const cancelledBadge = screen.getByText('cancelled');
		expect(cancelledBadge).toHaveClass('bg-red-100', 'text-red-800');
		
		const unknownBadge = screen.getByText('unknown');
		expect(unknownBadge).toHaveClass('bg-gray-100', 'text-gray-800');
	});

	it('renders responsive grid layout', () => {
		render(MangaGrid, { manga: mockManga });
		
		const grid = document.querySelector('.grid');
		expect(grid).toHaveClass(
			'grid-cols-2',
			'sm:grid-cols-3', 
			'md:grid-cols-4',
			'lg:grid-cols-5',
			'xl:grid-cols-6'
		);
	});

	it('maintains aspect ratio for cover images', () => {
		render(MangaGrid, { manga: [mockManga[0]] });
		
		const imageContainer = document.querySelector('.aspect-\\[3\\/4\\]');
		expect(imageContainer).toBeInTheDocument();
	});

	it('handles empty description gracefully', () => {
		const noDescManga: Manga = {
			...mockManga[0],
			description: undefined
		};
		
		render(MangaGrid, { manga: [noDescManga] });
		
		expect(screen.getByText('One Piece')).toBeInTheDocument();
		expect(screen.queryByText('A story about pirates')).not.toBeInTheDocument();
	});
});

describe('MangaGrid - Mobile/Responsive Tests', () => {
	let mockManga: Manga[];

	beforeEach(() => {
		vi.clearAllMocks();
		
		mockManga = [
			{
				id: 1,
				title: 'One Piece',
				slug: 'one-piece',
				author: 'Eiichiro Oda',
				description: 'A story about pirates and adventure on the high seas.',
				status: 'ongoing',
				total_chapters: 1000,
				cover_image: '/covers/one-piece.jpg'
			},
			{
				id: 2,
				title: 'Naruto',
				slug: 'naruto',
				author: 'Masashi Kishimoto',
				description: 'A young ninja seeks recognition from his peers.',
				status: 'completed',
				total_chapters: 700,
				cover_image: '/covers/naruto.jpg'
			}
		];
	});

	it('has responsive grid layout classes', () => {
		const { container } = render(MangaGrid, { manga: mockManga });
		
		const grid = container.querySelector('.grid');
		expect(grid).toBeInTheDocument();
		
		// Check for responsive grid classes
		const gridClasses = grid?.className;
		expect(gridClasses).toContain('grid-cols-2'); // Mobile default
		expect(gridClasses).toContain('sm:grid-cols-3'); // Small screens
		expect(gridClasses).toContain('md:grid-cols-4'); // Medium screens
		expect(gridClasses).toContain('lg:grid-cols-5'); // Large screens
		expect(gridClasses).toContain('xl:grid-cols-6'); // Extra large screens
	});

	it('uses proper spacing for mobile layouts', () => {
		const { container } = render(MangaGrid, { manga: mockManga });
		
		const grid = container.querySelector('.grid');
		const gridClasses = grid?.className;
		
		// Check for responsive gap classes
		expect(gridClasses).toContain('gap-4'); // Default gap
		expect(gridClasses).toContain('md:gap-6'); // Larger gap on medium+ screens
	});

	it('properly sizes cover images for mobile', () => {
		render(MangaGrid, { manga: [mockManga[0]] });
		
		const coverImage = screen.getByAltText('One Piece') as HTMLImageElement;
		
		// Should request appropriately sized images for mobile
		expect(apiClient.getCoverImageUrl).toHaveBeenCalledWith(1, { 
			width: 300, 
			height: 400 
		});
	});

	it('truncates long titles on mobile devices', () => {
		const longTitleManga: Manga = {
			...mockManga[0],
			title: 'Very Long Title That Should Be Truncated On Mobile Devices Because Screen Space Is Limited'
		};
		
		render(MangaGrid, { manga: [longTitleManga] });
		
		const titleElement = screen.getByText('Very Long Title That Should Be Truncated On Mob...');
		expect(titleElement).toBeInTheDocument();
		
		// Check for text truncation classes
		expect(titleElement.className).toContain('truncate');
	});

	it('truncates long author names for mobile', () => {
		const longAuthorManga: Manga = {
			...mockManga[0],
			author: 'Very Long Author Name That Should Be Truncated On Small Screens'
		};
		
		render(MangaGrid, { manga: [longAuthorManga] });
		
		const authorElement = screen.getByText(/by Very Long Author Name That Should Be Trunca.../);
		expect(authorElement).toBeInTheDocument();
		expect(authorElement.className).toContain('truncate');
	});

	it('uses mobile-friendly touch targets', async () => {
		const user = userEvent.setup();
		render(MangaGrid, { manga: [mockManga[0]] });
		
		const mangaCard = screen.getByRole('button', { name: /One Piece/ });
		
		// Cards should be large enough for touch interaction
		const cardElement = mangaCard.closest('.group');
		expect(cardElement).toBeInTheDocument();
		
		// Test touch interaction
		await user.click(mangaCard);
		expect(goto).toHaveBeenCalledWith('/manga/one-piece');
	});

	it('maintains proper aspect ratios on all screen sizes', () => {
		const { container } = render(MangaGrid, { manga: [mockManga[0]] });
		
		const imageContainer = container.querySelector('.aspect-\\[3\\/4\\]');
		expect(imageContainer).toBeInTheDocument();
		
		// Should maintain 3:4 aspect ratio across all devices
		const computedStyle = window.getComputedStyle(imageContainer!);
		// Note: In actual browser test, would check computed aspect-ratio
		expect(imageContainer?.className).toContain('aspect-[3/4]');
	});

	it('has proper responsive text sizing', () => {
		render(MangaGrid, { manga: [mockManga[0]] });
		
		const titleElement = screen.getByText('One Piece');
		const authorElement = screen.getByText('by Eiichiro Oda');
		const chaptersElement = screen.getByText('1000 ch');
		
		// Check for responsive text size classes
		expect(titleElement.className).toMatch(/text-(sm|base|lg)/);
		expect(authorElement.className).toMatch(/text-(xs|sm)/);
		expect(chaptersElement.className).toMatch(/text-(xs|sm)/);
	});

	it('handles no cover image gracefully on mobile', () => {
		const noCoverManga: Manga = {
			...mockManga[0],
			cover_image: null
		};
		
		render(MangaGrid, { manga: [noCoverManga] });
		
		const fallbackImage = screen.getByAltText('One Piece') as HTMLImageElement;
		expect(fallbackImage).toBeInTheDocument();
		
		// Should still request a placeholder/fallback image
		expect(apiClient.getCoverImageUrl).toHaveBeenCalled();
	});

	it('provides accessible labels for screen readers', () => {
		render(MangaGrid, { manga: [mockManga[0]] });
		
		const mangaCard = screen.getByRole('button');
		expect(mangaCard).toHaveAttribute('aria-label');
		
		const coverImage = screen.getByAltText('One Piece');
		expect(coverImage).toBeInTheDocument();
	});

	it('supports keyboard navigation on mobile devices with keyboards', async () => {
		const user = userEvent.setup();
		render(MangaGrid, { manga: mockManga });
		
		const firstCard = screen.getByRole('button', { name: /One Piece/ });
		const secondCard = screen.getByRole('button', { name: /Naruto/ });
		
		// Should be able to tab through cards
		await user.tab();
		expect(firstCard).toHaveFocus();
		
		await user.tab();
		expect(secondCard).toHaveFocus();
		
		// Should be able to activate with Enter
		await user.keyboard('{Enter}');
		expect(goto).toHaveBeenCalledWith('/manga/naruto');
	});
});