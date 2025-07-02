// Enhanced test setup file
import '@testing-library/jest-dom';
import { TextEncoder, TextDecoder } from 'util';
import 'jest-canvas-mock'; // Add this line

// Mock native modules that cause issues in Jest environment
const originalRequire = require;
global.require = (moduleName) => {
  if (moduleName === 'canvas' || moduleName === 'canvas/lib/bindings') {
    return {}; // Return an empty object for canvas and its bindings
  }
  try {
    return originalRequire(moduleName);
  } catch (e) {
    // Fallback for modules that might not be found in the mocked environment
    console.warn(`Could not load module: ${moduleName}. Error: ${e.message}`);
    return {};
  }
};

// Polyfills for Node environment
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

// Mock localStorage with enhanced functionality
const createEnhancedStorageMock = () => {
  let store = {};
  
  return {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value;
    }),
    removeItem: jest.fn((key) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
    get length() {
      return Object.keys(store).length;
    },
    key: jest.fn((index) => Object.keys(store)[index] || null),
    // Helper to reset store for tests
    __reset: () => {
      store = {};
    }
  };
};

const localStorageMock = createEnhancedStorageMock();
const sessionStorageMock = createEnhancedStorageMock();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true
});

Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
  writable: true
});

// Enhanced fetch mock
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    status: 200,
    statusText: 'OK',
    headers: new Headers(),
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
    blob: () => Promise.resolve(new Blob()),
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
    clone: function() { return this; }
  })
);

// Mock browser APIs
global.IntersectionObserver = jest.fn(function(callback) {
  this.observe = jest.fn();
  this.unobserve = jest.fn();
  this.disconnect = jest.fn();
  return this;
});

global.ResizeObserver = jest.fn(function(callback) {
  this.observe = jest.fn();
  this.unobserve = jest.fn();
  this.disconnect = jest.fn();
  return this;
});

global.MutationObserver = jest.fn(function(callback) {
  this.observe = jest.fn();
  this.disconnect = jest.fn();
  this.takeRecords = jest.fn();
  return this;
});

// Mock URL and File APIs
global.URL.createObjectURL = jest.fn(() => 'mock-object-url');
global.URL.revokeObjectURL = jest.fn();

global.File = jest.fn(() => ({
  name: 'test-file.pdf',
  type: 'application/pdf',
  size: 1024
}));

global.FileReader = jest.fn(() => ({
  readAsDataURL: jest.fn(),
  readAsText: jest.fn(),
  readAsArrayBuffer: jest.fn(),
  result: null,
  onload: null,
  onerror: null
}));

// Mock Canvas API
HTMLCanvasElement.prototype.getContext = jest.fn(() => ({
  fillRect: jest.fn(),
  clearRect: jest.fn(),
  getImageData: jest.fn(() => ({
    data: new Uint8ClampedArray(4)
  })),
  putImageData: jest.fn(),
  createImageData: jest.fn(() => []),
  setTransform: jest.fn(),
  drawImage: jest.fn(),
  save: jest.fn(),
  fillText: jest.fn(),
  restore: jest.fn(),
  beginPath: jest.fn(),
  moveTo: jest.fn(),
  lineTo: jest.fn(),
  closePath: jest.fn(),
  stroke: jest.fn(),
  translate: jest.fn(),
  scale: jest.fn(),
  rotate: jest.fn(),
  arc: jest.fn(),
  fill: jest.fn(),
  measureText: jest.fn(() => ({ width: 0 })),
  transform: jest.fn(),
  rect: jest.fn(),
  clip: jest.fn()
}));

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock window methods
global.alert = jest.fn();
global.confirm = jest.fn(() => true);
global.prompt = jest.fn(() => 'test input');

// Mock WebSocket
global.WebSocket = jest.fn(function(url) {
  this.close = jest.fn();
  this.send = jest.fn();
  this.readyState = 1; // OPEN
  this.url = url;
  this.onopen = null;
  this.onclose = null;
  this.onmessage = null;
  this.onerror = null;
  return this;
});
global.WebSocket.CONNECTING = 0;
global.WebSocket.OPEN = 1;
global.WebSocket.CLOSING = 2;
global.WebSocket.CLOSED = 3;

// Mock notification API
global.Notification = jest.fn(() => ({
  close: jest.fn()
}));
global.Notification.permission = 'granted';
global.Notification.requestPermission = jest.fn(() => Promise.resolve('granted'));

// Mock scrollTo
window.scrollTo = jest.fn();
Element.prototype.scrollTo = jest.fn();
Element.prototype.scrollIntoView = jest.fn();

// Mock console methods for cleaner test output
const originalError = console.error;
const originalWarn = console.warn;

beforeAll(() => {
  console.error = jest.fn();
  console.warn = jest.fn();
});

afterAll(() => {
  console.error = originalError;
  console.warn = originalWarn;
});

// Mock PDF.js worker
if (typeof global.pdfjsLib !== 'undefined') {
  global.pdfjsLib.GlobalWorkerOptions.workerSrc = 'mock-worker.js';
}

// Mock react-beautiful-dnd
jest.mock('react-beautiful-dnd', () => ({
  DragDropContext: ({ children }) => children,
  Droppable: ({ children }) => children({
    draggableProps: {},
    dragHandleProps: {},
    innerRef: jest.fn()
  }, {}),
  Draggable: ({ children }) => children({
    draggableProps: {},
    dragHandleProps: {},
    innerRef: jest.fn()
  }, {})
}));

// Mock react-pdf
jest.mock('react-pdf', () => ({
  Document: ({ children, onLoadSuccess }) => {
    if (onLoadSuccess) {
      onLoadSuccess({ numPages: 2 });
    }
    return children;
  },
  Page: ({ onLoadSuccess }) => {
    if (onLoadSuccess) {
      onLoadSuccess();
    }
    return 'Mock PDF Page';
  },
  pdfjs: {
    GlobalWorkerOptions: {
      workerSrc: 'mock-worker.js'
    }
  }
}));

// Mock NotificationProvider
jest.mock('../components/NotificationProvider', () => ({
  useNotifications: () => ({
    notifications: [],
    isConnected: true,
    connectionStatus: 'connected',
    addNotification: jest.fn(),
    markAsRead: jest.fn(),
    markAllAsRead: jest.fn(),
    removeNotification: jest.fn(),
    clearAllNotifications: jest.fn(),
    joinRoom: jest.fn(),
    leaveRoom: jest.fn(),
    sendMessage: jest.fn(),
    connectWebSocket: jest.fn(),
    disconnectWebSocket: jest.fn(),
    unreadCount: 0
  }),
  default: ({ children }) => children
}));

// Mock crypto for UUID generation in tests
Object.defineProperty(global, 'crypto', {
  value: {
    randomUUID: () => 'mock-uuid-' + Date.now(),
    getRandomValues: (arr) => {
      for (let i = 0; i < arr.length; i++) {
        arr[i] = Math.floor(Math.random() * 256);
      }
      return arr;
    }
  }
});

// Global test cleanup
beforeEach(() => {
  // Reset fetch mock to default behavior
  fetch.mockResolvedValue({
    ok: true,
    status: 200,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
    blob: () => Promise.resolve(new Blob())
  });
  
  // Note: Don't reset storage or all mocks as it interferes with individual tests
});

afterEach(() => {
  // Clean up any remaining timers
  jest.clearAllTimers();
  jest.useRealTimers();
});

// Global error handler for unhandled promise rejections in tests
process.on('unhandledRejection', (reason, promise) => {
  console.log('Unhandled Rejection at:', promise, 'reason:', reason);
  // Optionally fail the test
  // throw new Error('Unhandled promise rejection in test');
});

// Increase timeout for slower tests
jest.setTimeout(30000);

// Export test utilities
export {
  localStorageMock,
  sessionStorageMock
};