module.exports = {
  // Test environment
  testEnvironment: 'jsdom',
  
  // Setup files
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.js'],
  
  // Module paths
  moduleDirectories: ['node_modules', 'src'],
  
  // Module name mapping for CSS/asset imports
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(gif|ttf|eot|svg|png|jpg|jpeg|webp)$': '<rootDir>/src/__mocks__/fileMock.js',
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@services/(.*)$': '<rootDir>/src/services/$1',
    '^@test-utils/(.*)$': '<rootDir>/src/test-utils/$1'
  },
  
  // Test file patterns
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{js,jsx,ts,tsx}',
    '<rootDir>/src/**/*.(test|spec).{js,jsx,ts,tsx}'
  ],
  
  // Files to ignore
  testPathIgnorePatterns: [
    '<rootDir>/node_modules/',
    '<rootDir>/build/',
    '<rootDir>/coverage/',
    '<rootDir>/tests_e2e/'
  ],
  
  // Module file extensions
  moduleFileExtensions: ['js', 'jsx', 'json', 'ts', 'tsx'],
  
  // Transform files
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': ['babel-jest', {
      presets: [
        ['@babel/preset-env', { 
          targets: { node: 'current' },
          modules: 'auto'
        }],
        ['@babel/preset-react', { runtime: 'automatic' }]
      ],
      plugins: [
        '@babel/plugin-transform-class-properties',
        '@babel/plugin-transform-private-methods',
        ['@babel/plugin-proposal-private-property-in-object', { loose: true }]
      ]
    }],
    '^.+\\.css$': 'jest-transform-css'
  },
  
  // Transform ignore patterns
  transformIgnorePatterns: [
    'node_modules/(?!(react-pdf|pdfjs-dist|react-beautiful-dnd)/)'
  ],
  
  // Coverage configuration
  collectCoverage: true,
  collectCoverageFrom: [
    'src/**/*.{js,jsx}',
    '!src/index.js',
    '!src/reportWebVitals.js',
    '!src/**/*.stories.{js,jsx}',
    '!src/**/__tests__/**',
    '!src/**/test-utils/**',
    '!src/**/*.test.{js,jsx}',
    '!src/**/*.spec.{js,jsx}',
    '!**/node_modules/**',
    '!**/vendor/**'
  ],
  
  // Coverage thresholds
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    },
    './src/components/': {
      branches: 85,
      functions: 85,
      lines: 85,
      statements: 85
    }
  },
  
  // Coverage reporters
  coverageReporters: [
    'text',
    'lcov',
    'html',
    'json-summary',
    'clover'
  ],
  
  // Coverage directory
  coverageDirectory: '<rootDir>/coverage',
  
  // Test timeout
  testTimeout: 30000,
  
  // Verbose output
  verbose: true,
  
  // Clear mocks between tests
  clearMocks: true,
  restoreMocks: true,
  
  // Global setup/teardown
  globalSetup: undefined,
  globalTeardown: undefined,
  
  // Watch mode settings
  watchPathIgnorePatterns: [
    '<rootDir>/node_modules/',
    '<rootDir>/build/',
    '<rootDir>/coverage/'
  ],
  
  // Error handling
  errorOnDeprecated: false,
  
  // Snapshot settings
  snapshotSerializers: [],
  
  // Custom test environment options
  testEnvironmentOptions: {
    url: 'http://localhost:3000'
  },
  
  // Reporter options
  reporters: [
    'default',
    ['jest-html-reporters', {
      publicPath: './coverage/html-report',
      filename: 'test-report.html',
      expand: true,
      hideIcon: false
    }]
  ],
  
  // Maximum number of workers
  maxWorkers: '50%',
  
  // Bail after first test failure in CI
  bail: process.env.CI ? 1 : 0,
  
  // Force exit after tests complete
  forceExit: true,
  
  // Detect open handles
  detectOpenHandles: false
};