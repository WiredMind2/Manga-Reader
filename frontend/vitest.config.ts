import { defineConfig } from 'vitest/config';
import { svelte, vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import path from 'path';

export default defineConfig({
	plugins: [
		svelte({
			preprocess: vitePreprocess(),
			compilerOptions: {
				// Empty compiler options - let svelte.config.js handle compatibility mode
			}
		})
	],
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}'],
		environment: 'jsdom',
		setupFiles: ['./src/tests/setup.ts'],
		globals: true,
		// Use browser mode for Svelte components
		browser: {
			enabled: false, // We'll use jsdom for now
			name: 'chromium'
		},
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
	},
	resolve: {
		alias: {
			$lib: path.resolve(__dirname, './src/lib'),
			$app: path.resolve(__dirname, './src/mocks/app')
		},
		conditions: ['browser']
	}
});