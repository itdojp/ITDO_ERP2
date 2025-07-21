import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig({
  plugins: [
    react(),
    visualizer({
      filename: 'dist/bundle-analysis.html',
      open: process.env.ANALYZE === 'true',
      gzipSize: true,
      brotliSize: true,
      template: 'treemap', // Options: treemap, sunburst, network
    })
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    }
  },
  build: {
    target: 'esnext',
    minify: 'esbuild',
    sourcemap: true,
    reportCompressedSize: true,
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          // Core React
          'react-vendor': ['react', 'react-dom'],
          
          // State Management
          'state-management': ['@tanstack/react-query'],
          
          // UI Libraries  
          'ui-icons': ['lucide-react'],
          'ui-utils': ['clsx', 'tailwind-merge', 'class-variance-authority'],
          
          // Charts and Visualization
          'charts': ['recharts'],
          
          // Date and Time
          'date-utils': ['date-fns'],
          
          // Form Handling
          'forms': ['react-hook-form', 'zod'],
          
          // Router
          'router': ['react-router-dom'],
          
          // Performance and Utilities
          'performance': ['./src/hooks/usePerformanceMonitor', './src/hooks/useVirtualization'],
          'optimization': ['./src/hooks/useMemoizedCallback', './src/utils/performanceOptimization']
        },
        chunkFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId
          if (facadeModuleId) {
            if (facadeModuleId.includes('node_modules')) {
              return 'vendor/[name]-[hash].js'
            }
            if (facadeModuleId.includes('src/components')) {
              return 'components/[name]-[hash].js'
            }
            if (facadeModuleId.includes('src/pages')) {
              return 'pages/[name]-[hash].js'
            }
            if (facadeModuleId.includes('src/hooks')) {
              return 'hooks/[name]-[hash].js'
            }
            if (facadeModuleId.includes('src/services')) {
              return 'services/[name]-[hash].js'
            }
          }
          return 'chunks/[name]-[hash].js'
        },
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name?.split('.') || []
          const ext = info[info.length - 1]
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
            return `assets/images/[name]-[hash][extname]`
          }
          if (/woff2?|eot|ttf|otf/i.test(ext)) {
            return `assets/fonts/[name]-[hash][extname]`
          }
          return `assets/[name]-[hash][extname]`
        }
      }
    },
    // Optimization settings
    cssCodeSplit: true,
    assetsInlineLimit: 4096, // 4kb inline threshold
  },
  // Performance optimization settings
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@tanstack/react-query',
      'lucide-react',
      'clsx',
      'tailwind-merge'
    ],
    exclude: ['@vite/client', '@vite/env']
  },
  // Bundle analysis specific settings
  define: {
    __BUNDLE_ANALYSIS__: JSON.stringify(true),
    __BUILD_TIME__: JSON.stringify(new Date().toISOString())
  }
})