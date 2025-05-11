module.exports = {
    // The test environment that will be used for testing
    testEnvironment: 'jsdom',
    
    // Transform files with these extensions using the specified transformers
    transform: {
      '^.+\\.(js|jsx)$': 'babel-jest',
      '^.+\\.(ts|tsx)$': 'ts-jest'
    },
    
    // Files to ignore during testing
    testPathIgnorePatterns: ['/node_modules/', '/build/'],
    
    // Setup files to run before each test
    setupFilesAfterEnv: ['<rootDir>/src/setupTests.js'],
    
    // Module file extensions for importing
    moduleFileExtensions: ['js', 'jsx', 'ts', 'tsx', 'json'],
    
    // Mock CSS and image imports
    moduleNameMapper: {
      '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
      '\\.(jpg|jpeg|png|gif|webp|svg)$': '<rootDir>/__mocks__/fileMock.js'
    },
    
    // Root directories for module resolution
    roots: ['<rootDir>/src'],
    
    // Module directory names
    moduleDirectories: ['node_modules', 'src']
  };