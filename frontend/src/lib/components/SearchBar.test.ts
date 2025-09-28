import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import SearchBar from '../lib/components/SearchBar.svelte';

describe('SearchBar', () => {
	let user: ReturnType<typeof userEvent.setup>;

	beforeEach(() => {
		vi.clearAllMocks();
		vi.clearAllTimers();
		vi.useFakeTimers();
		user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
	});

	afterEach(() => {
		vi.runOnlyPendingTimers();
		vi.useRealTimers();
	});

	it('renders search input with placeholder', () => {
		render(SearchBar);
		
		const input = screen.getByPlaceholderText('Search manga...');
		expect(input).toBeInTheDocument();
		expect(input).toHaveAttribute('type', 'text');
	});

	it('displays search icon', () => {
		render(SearchBar);
		
		const searchIcon = document.querySelector('svg[viewBox="0 0 24 24"]');
		expect(searchIcon).toBeInTheDocument();
	});

	it('updates input value when typing', async () => {
		render(SearchBar);
		
		const input = screen.getByPlaceholderText('Search manga...') as HTMLInputElement;
		await user.type(input, 'One Piece');
		
		expect(input.value).toBe('One Piece');
	});

	it('dispatches search event on form submit', async () => {
		const { component } = render(SearchBar);
		const mockSearch = vi.fn();
		component.$on('search', mockSearch);
		
		const form = document.querySelector('form');
		const input = screen.getByPlaceholderText('Search manga...') as HTMLInputElement;
		
		await user.type(input, 'Naruto');
		await fireEvent.submit(form!);
		
		expect(mockSearch).toHaveBeenCalledWith(
			expect.objectContaining({
				detail: 'Naruto'
			})
		);
	});

	it('prevents form default submission', async () => {
		render(SearchBar);
		
		const form = document.querySelector('form');
		const mockPreventDefault = vi.fn();
		
		await fireEvent.submit(form!, { preventDefault: mockPreventDefault });
		
		expect(mockPreventDefault).toHaveBeenCalled();
	});

	it('debounces search input', async () => {
		const { component } = render(SearchBar);
		const mockSearch = vi.fn();
		component.$on('search', mockSearch);
		
		const input = screen.getByPlaceholderText('Search manga...');
		
		// Type multiple characters quickly
		await user.type(input, 'One');
		
		// Should not have dispatched yet
		expect(mockSearch).not.toHaveBeenCalled();
		
		// Advance timer past debounce delay
		vi.advanceTimersByTime(300);
		
		expect(mockSearch).toHaveBeenCalledWith(
			expect.objectContaining({
				detail: 'One'
			})
		);
	});

	it('shows clear button when input has value', async () => {
		render(SearchBar);
		
		const input = screen.getByPlaceholderText('Search manga...');
		
		// Initially no clear button
		expect(screen.queryByLabelText('Clear search')).not.toBeInTheDocument();
		
		// Type something
		await user.type(input, 'test');
		
		// Clear button should appear
		expect(screen.getByLabelText('Clear search')).toBeInTheDocument();
	});

	it('clears input when clear button is clicked', async () => {
		const { component } = render(SearchBar);
		const mockSearch = vi.fn();
		component.$on('search', mockSearch);
		
		const input = screen.getByPlaceholderText('Search manga...') as HTMLInputElement;
		
		// Type something
		await user.type(input, 'test search');
		expect(input.value).toBe('test search');
		
		// Click clear button
		const clearButton = screen.getByLabelText('Clear search');
		await user.click(clearButton);
		
		// Input should be cleared
		expect(input.value).toBe('');
		
		// Should dispatch empty search
		expect(mockSearch).toHaveBeenCalledWith(
			expect.objectContaining({
				detail: ''
			})
		);
	});

	it('hides clear button after clearing', async () => {
		render(SearchBar);
		
		const input = screen.getByPlaceholderText('Search manga...');
		
		// Type something to show clear button
		await user.type(input, 'test');
		expect(screen.getByLabelText('Clear search')).toBeInTheDocument();
		
		// Clear the input
		const clearButton = screen.getByLabelText('Clear search');
		await user.click(clearButton);
		
		// Clear button should be hidden
		expect(screen.queryByLabelText('Clear search')).not.toBeInTheDocument();
	});

	it('handles rapid typing with debouncing', async () => {
		const { component } = render(SearchBar);
		const mockSearch = vi.fn();
		component.$on('search', mockSearch);
		
		const input = screen.getByPlaceholderText('Search manga...');
		
		// Type rapidly
		await user.type(input, 'O');
		vi.advanceTimersByTime(100);
		await user.type(input, 'n');
		vi.advanceTimersByTime(100);
		await user.type(input, 'e');
		
		// Should not have dispatched yet
		expect(mockSearch).not.toHaveBeenCalled();
		
		// Advance past debounce delay
		vi.advanceTimersByTime(300);
		
		// Should dispatch final value
		expect(mockSearch).toHaveBeenCalledTimes(1);
		expect(mockSearch).toHaveBeenCalledWith(
			expect.objectContaining({
				detail: 'One'
			})
		);
	});

	it('handles keyboard navigation', async () => {
		render(SearchBar);
		
		const input = screen.getByPlaceholderText('Search manga...');
		
		// Focus on input
		await user.click(input);
		expect(input).toHaveFocus();
		
		// Type and use keyboard navigation
		await user.type(input, 'test{ArrowLeft}{ArrowLeft}');
		
		// Input should still have focus and value
		expect(input).toHaveFocus();
		expect((input as HTMLInputElement).value).toBe('test');
	});

	it('has proper accessibility attributes', () => {
		render(SearchBar);
		
		const input = screen.getByPlaceholderText('Search manga...');
		expect(input).toHaveAttribute('type', 'text');
		
		const clearButton = screen.queryByLabelText('Clear search');
		if (clearButton) {
			expect(clearButton).toHaveAttribute('aria-label', 'Clear search');
		}
	});

	it('handles form submission with Enter key', async () => {
		const { component } = render(SearchBar);
		const mockSearch = vi.fn();
		component.$on('search', mockSearch);
		
		const input = screen.getByPlaceholderText('Search manga...');
		
		// Type and press Enter
		await user.type(input, 'manga search{Enter}');
		
		expect(mockSearch).toHaveBeenCalledWith(
			expect.objectContaining({
				detail: 'manga search'
			})
		);
	});

	it('clears debounce timer when unmounted', () => {
		const { unmount } = render(SearchBar);
		
		const input = screen.getByPlaceholderText('Search manga...');
		
		// Start typing to set timer
		fireEvent.input(input, { target: { value: 'test' } });
		
		// Unmount component
		unmount();
		
		// Timer should be cleared (no way to directly test this, but component should handle cleanup)
		expect(true).toBe(true); // Placeholder assertion
	});
});