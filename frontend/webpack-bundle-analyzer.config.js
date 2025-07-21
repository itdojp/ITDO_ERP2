const { defineConfig } = require('vite')
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer')
const path = require('path')

module.exports = defineConfig({
  plugins: [
    new BundleAnalyzerPlugin({
      analyzerMode: process.env.ANALYZE ? 'server' : 'json',
      reportFilename: 'bundle-report.html',
      generateStatsFile: true,
      statsFilename: 'bundle-stats.json',
      openAnalyzer: process.env.ANALYZE === 'true',
      logLevel: 'info'
    })
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['lucide-react'],
          query: ['@tanstack/react-query'],
          charts: ['recharts'],
          utils: ['clsx', 'tailwind-merge']
        }
      }
    },
    sourcemap: true,
    reportCompressedSize: true
  }
})