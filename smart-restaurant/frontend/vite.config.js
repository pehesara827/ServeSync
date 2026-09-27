import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Enables JSX and React fast refresh in Vite.
export default defineConfig({ plugins: [react()] });