// Jest configuration for frontend testing
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/frontend/src/setupTests.js'],
  moduleNameMapper: {
    '\.(css|less|scss|sass)
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': ['babel-jest', {
      presets: [
        ['@babel/preset-env', { targets: { node: 'current' } }],
        ['@babel/preset-react', { runtime: 'automatic' }]
      ]
    }],
    '^.+\\.(css|less|scss|sass)$': 'jest-transform-stub'
  },
  testMatch: [
    '<rootDir>/frontend/src/**/__tests__/**/*.{js,jsx,ts,tsx}',
    '<rootDir>/frontend/src/**/*.(test|spec).{js,jsx,ts,tsx}'
  ],
  collectCoverageFrom: [
    'frontend/src/**/*.{js,jsx}',
    '!frontend/src/index.js',
    '!frontend/src/reportWebVitals.js',
    '!frontend/src/**/*.stories.{js,jsx}',
    '!frontend/src/**/*.test.{js,jsx}',
    '!frontend/src/__mocks__/**'
  ],
  coverageReporters: ['text', 'lcov', 'json-summary'],
  coverageDirectory: 'frontend/coverage',
  testResultsProcessor: 'jest-json-reporter',
  reporters: [
    'default',
    ['jest-json-reporter', {
      outputPath: 'frontend/test-results.json'
    }]
  ],
  moduleDirectories: ['node_modules', 'frontend/src'],
  testTimeout: 10000,
  
  // Globals for React Testing Library
  globals: {
    'ts-jest': {
      useESM: true
    }
  }
};: 'identity-obj-proxy',
    '\.(gif|ttf|eot|svg|png)
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': ['babel-jest', {
      presets: [
        ['@babel/preset-env', { targets: { node: 'current' } }],
        ['@babel/preset-react', { runtime: 'automatic' }]
      ]
    }],
    '^.+\\.(css|less|scss|sass)$': 'jest-transform-stub'
  },
  testMatch: [
    '<rootDir>/frontend/src/**/__tests__/**/*.{js,jsx,ts,tsx}',
    '<rootDir>/frontend/src/**/*.(test|spec).{js,jsx,ts,tsx}'
  ],
  collectCoverageFrom: [
    'frontend/src/**/*.{js,jsx}',
    '!frontend/src/index.js',
    '!frontend/src/reportWebVitals.js',
    '!frontend/src/**/*.stories.{js,jsx}',
    '!frontend/src/**/*.test.{js,jsx}',
    '!frontend/src/__mocks__/**'
  ],
  coverageReporters: ['text', 'lcov', 'json-summary'],
  coverageDirectory: 'frontend/coverage',
  testResultsProcessor: 'jest-json-reporter',
  reporters: [
    'default',
    ['jest-json-reporter', {
      outputPath: 'frontend/test-results.json'
    }]
  ],
  moduleDirectories: ['node_modules', 'frontend/src'],
  testTimeout: 10000,
  
  // Globals for React Testing Library
  globals: {
    'ts-jest': {
      useESM: true
    }
  }
};: '<rootDir>/frontend/src/__mocks__/fileMock.js'
  },
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': ['babel-jest', {
      presets: [
        ['@babel/preset-env', { targets: { node: 'current' } }],
        ['@babel/preset-react', { runtime: 'automatic' }]
      ]
    }],
    '^.+\\.(css|less|scss|sass)$': 'jest-transform-stub'
  },
  testMatch: [
    '<rootDir>/frontend/src/**/__tests__/**/*.{js,jsx,ts,tsx}',
    '<rootDir>/frontend/src/**/*.(test|spec).{js,jsx,ts,tsx}'
  ],
  collectCoverageFrom: [
    'frontend/src/**/*.{js,jsx}',
    '!frontend/src/index.js',
    '!frontend/src/reportWebVitals.js',
    '!frontend/src/**/*.stories.{js,jsx}',
    '!frontend/src/**/*.test.{js,jsx}',
    '!frontend/src/__mocks__/**'
  ],
  coverageReporters: ['text', 'lcov', 'json-summary'],
  coverageDirectory: 'frontend/coverage',
  testResultsProcessor: 'jest-json-reporter',
  reporters: [
    'default',
    ['jest-json-reporter', {
      outputPath: 'frontend/test-results.json'
    }]
  ],
  moduleDirectories: ['node_modules', 'frontend/src'],
  testTimeout: 10000,
  
  // Globals for React Testing Library
  globals: {
    'ts-jest': {
      useESM: true
    }
  }
};