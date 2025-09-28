import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import MangaGrid from '../lib/components/MangaGrid.svelte';
import type { Manga } from '../lib/api/types';

// Mock the navigation and API client
const mockGoto = vi.fn();
const mockApiClient = {
	getCoverImageUrl: vi.fn((id: number, options?: any) => 
		`https://api.example.com/covers/${id}?width=${options?.width}&height=${options?.height}`
	)
};

vi.mock('$app/navigation', () => ({
	goto: mockGoto
}));

vi.mock('../lib/api/client', () => ({
	apiClient: mockApiClient
}));

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
				status: 'completed',
				total_chapters: 700,
				cover_image: '/covers/naruto.jpg'
			},
			{
				id: 3,
				title: 'Very Long Title That Should Be Truncated Because It Exceeds The Character Limit',
				slug: 'long-title',
				author: 'Test Author With Very Long Name That Should Also Be Truncated',
				description: 'A very long description that should be truncated when displayed in the manga grid to ensure proper layout and readability.',
				status: 'hiatus',
				total_chapters: 50,
				cover_image: null
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
		expect(mockApiClient.getCoverImageUrl).toHaveBeenCalledWith(1, { width: 300, height: 400 });
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
		
		expect(mockGoto).toHaveBeenCalledWith('/manga/one-piece');
	});

	it('handles keyboard navigation', async () => {
		render(MangaGrid, { manga: [mockManga[0]] });
		
		const mangaCard = screen.getByRole('button');
		mangaCard.focus();
		await user.keyboard('{Enter}');
		
		expect(mockGoto).toHaveBeenCalledWith('/manga/one-piece');
	});

	it('handles read button click', async () => {
		render(MangaGrid, { manga: [mockManga[0]] });
		
		const readButton = screen.getByText('Read Now');
		await user.click(readButton);
		
		expect(mockGoto).toHaveBeenCalledWith('/manga/one-piece');
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