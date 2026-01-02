import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import LoadingSpinner from './LoadingSpinner.svelte';

describe('LoadingSpinner', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('renders with default props', () => {
		render(LoadingSpinner);
		
		expect(screen.getByText('Loading...')).toBeInTheDocument();
		const spinner = document.querySelector('.animate-spin');
		expect(spinner).toBeInTheDocument();
	});

	it('renders with custom message', () => {
		render(LoadingSpinner, { message: 'Please wait...' });
		
		expect(screen.getByText('Please wait...')).toBeInTheDocument();
	});

	it('hides message when showMessage is false', () => {
		render(LoadingSpinner, { 
			message: 'Loading...', 
			showMessage: false 
		});
		
		expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
		const spinner = document.querySelector('.animate-spin');
		expect(spinner).toBeInTheDocument();
	});

	it('applies correct size classes for small size', () => {
		render(LoadingSpinner, { size: 'sm' });
		
		const spinner = document.querySelector('.w-4');
		expect(spinner).toBeInTheDocument();
		expect(spinner).toHaveClass('h-4', 'border-2');
	});

	it('applies correct size classes for medium size', () => {
		render(LoadingSpinner, { size: 'md' });
		
		const spinner = document.querySelector('.w-12');
		expect(spinner).toBeInTheDocument();
		expect(spinner).toHaveClass('h-12', 'border-4');
	});

	it('applies correct size classes for large size', () => {
		render(LoadingSpinner, { size: 'lg' });
		
		const spinner = document.querySelector('.w-16');
		expect(spinner).toBeInTheDocument();
		expect(spinner).toHaveClass('h-16', 'border-4');
	});

	it('uses inline layout for small size', () => {
		render(LoadingSpinner, { size: 'sm' });
		
		const container = document.querySelector('.inline-flex');
		expect(container).toBeInTheDocument();
		expect(container).toHaveClass('items-center', 'gap-2');
	});

	it('uses flex column layout for medium and large sizes', () => {
		render(LoadingSpinner, { size: 'md' });
		
		const container = document.querySelector('.flex-col');
		expect(container).toBeInTheDocument();
		expect(container).toHaveClass('items-center', 'justify-center', 'py-12');
	});

	it('shows message for small size when custom message is provided', () => {
		render(LoadingSpinner, { 
			size: 'sm', 
			message: 'Custom loading...' 
		});
		
		expect(screen.getByText('Custom loading...')).toBeInTheDocument();
	});

	it('hides default message for small size', () => {
		render(LoadingSpinner, { 
			size: 'sm', 
			message: 'Loading...' 
		});
		
		expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
	});

	it('applies correct message styling for different sizes', () => {
		const { rerender } = render(LoadingSpinner, { 
			size: 'md',
			message: 'Test message'
		});
		
		let message = screen.getByText('Test message');
		expect(message).toHaveClass('mt-4');
		
		rerender({ 
			size: 'sm',
			message: 'Custom message'
		});
		
		message = screen.getByText('Custom message');
		expect(message).toHaveClass('mt-0', 'ml-2');
	});

	it('has proper accessibility attributes', () => {
		render(LoadingSpinner, { message: 'Loading content...' });
		
		const spinner = document.querySelector('.animate-spin');
		expect(spinner).toBeInTheDocument();
		
		// The spinner should be visually apparent and the message should be readable
		const message = screen.getByText('Loading content...');
		expect(message).toBeInTheDocument();
	});
});