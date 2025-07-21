import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import dts from 'vite-plugin-dts'
import { libInjectCss } from 'vite-plugin-lib-inject-css'

export default defineConfig({
  plugins: [
    react(),
    libInjectCss(),
    dts({
      include: ['src/components', 'src/hooks', 'src/lib', 'src/design-system'],
      exclude: ['src/**/*.test.tsx', 'src/**/*.stories.tsx', 'src/test/**/*'],
      rollupTypes: true,
    }),
  ],
  build: {
    lib: {
      entry: {
        index: resolve(__dirname, 'src/index.ts'),
        components: resolve(__dirname, 'src/components/index.ts'),
        hooks: resolve(__dirname, 'src/hooks/index.ts'),
        utils: resolve(__dirname, 'src/lib/index.ts'),
        'design-system': resolve(__dirname, 'src/design-system/index.ts'),
      },
      name: 'ITDOERPComponents',
      formats: ['es', 'umd'],
      fileName: (format, entryName) => `${entryName}.${format}.js`,
    },
    rollupOptions: {
      external: [
        'react',
        'react-dom',
        'react/jsx-runtime',
        '@tanstack/react-query',
        'lucide-react',
        'class-variance-authority',
        'clsx',
        'tailwind-merge',
      ],
      output: {
        globals: {
          'react': 'React',
          'react-dom': 'ReactDOM',
          'react/jsx-runtime': 'React',
          '@tanstack/react-query': 'ReactQuery',
          'lucide-react': 'LucideReact',
          'class-variance-authority': 'ClassVarianceAuthority',
          'clsx': 'clsx',
          'tailwind-merge': 'tailwindMerge',
        },
      },
    },
    sourcemap: true,
    emptyOutDir: true,
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
})