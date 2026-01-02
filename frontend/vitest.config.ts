import { defineConfig } from 'vitest/config';

export default defineConfig({
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}'],
		environment: 'jsdom',
		setupFiles: ['./src/tests/setup.ts'],
		globals: true,
		coverage: {
			reporter: ['text', 'json', 'html'],
			include: ['src/**/*.{js,ts,svelte}'],
			exclude: [
				'src/tests/**',
				'src/**/*.test.{js,ts,svelte}',
				'src/**/*.spec.{js,ts,svelte}',
				'src/app.html',
				'src/app.d.ts'
			]
		}
	}
});