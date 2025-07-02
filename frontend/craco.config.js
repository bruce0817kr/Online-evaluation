const path = require('path');
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');

module.exports = {
  webpack: {
    configure: (webpackConfig, { env, paths }) => {
      // Production optimizations
      if (env === 'production') {
        // Code splitting optimization
        webpackConfig.optimization = {
          ...webpackConfig.optimization,
          splitChunks: {
            chunks: 'all',
            cacheGroups: {
              vendor: {
                test: /[\\/]node_modules[\\/]/,
                name: 'vendors',
                priority: 10,
                chunks: 'all',
              },
              react: {
                test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
                name: 'react',
                priority: 20,
                chunks: 'all',
              },
              pdf: {
                test: /[\\/]node_modules[\\/](pdfjs-dist|react-pdf)[\\/]/,
                name: 'pdf',
                priority: 15,
                chunks: 'all',
              },
              common: {
                name: 'common',
                minChunks: 2,
                priority: 5,
                chunks: 'all',
                enforce: true
              }
            }
          },
          runtimeChunk: {
            name: 'runtime'
          },
          usedExports: true,
          sideEffects: false
        };

        // Cache optimization
        webpackConfig.cache = {
          type: 'filesystem',
          buildDependencies: {
            config: [__filename]
          },
          cacheDirectory: path.resolve(__dirname, 'node_modules/.cache/webpack'),
          compression: 'gzip'
        };

        // Performance optimizations
        webpackConfig.performance = {
          maxAssetSize: 512000,
          maxEntrypointSize: 512000,
          hints: 'warning'
        };

        // Module resolution optimization
        webpackConfig.resolve = {
          ...webpackConfig.resolve,
          modules: [
            path.resolve(__dirname, 'src'),
            'node_modules'
          ],
          alias: {
            ...webpackConfig.resolve.alias,
            '@': path.resolve(__dirname, 'src'),
            '@components': path.resolve(__dirname, 'src/components'),
            '@utils': path.resolve(__dirname, 'src/utils'),
            '@styles': path.resolve(__dirname, 'src/styles')
          }
        };

        // Tree shaking optimization
        webpackConfig.module.rules.push({
          test: /\.js$/,
          exclude: /node_modules/,
          use: {
            loader: 'babel-loader',
            options: {
              presets: [
                ['@babel/preset-env', { 
                  modules: false,
                  useBuiltIns: 'usage',
                  corejs: 3
                }],
                '@babel/preset-react'
              ],
              plugins: [
                '@babel/plugin-syntax-dynamic-import'
              ]
            }
          }
        });

        // Bundle analyzer (only when ANALYZE=true)
        if (process.env.ANALYZE === 'true') {
          webpackConfig.plugins.push(
            new BundleAnalyzerPlugin({
              analyzerMode: 'static',
              openAnalyzer: false,
              reportFilename: 'bundle-report.html'
            })
          );
        }
      }

      // Development optimizations
      if (env === 'development') {
        // Fast refresh and HMR optimization
        webpackConfig.cache = {
          type: 'memory'
        };
        
        // Faster development builds
        webpackConfig.optimization = {
          ...webpackConfig.optimization,
          removeAvailableModules: false,
          removeEmptyChunks: false,
          splitChunks: false
        };
      }

      return webpackConfig;
    }
  },
  // ESLint disable for faster builds
  eslint: {
    enable: false
  },
  // TypeScript checking optimization
  typescript: {
    enableTypeChecking: false
  }
};