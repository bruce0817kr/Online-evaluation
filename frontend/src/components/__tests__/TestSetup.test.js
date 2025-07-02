import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

// Simple component for testing
const SimpleTestComponent = () => {
  return <div>Test Setup Works</div>;
};

describe('Test Setup Verification', () => {
  test('basic test setup works', () => {
    render(<SimpleTestComponent />);
    expect(screen.getByText('Test Setup Works')).toBeInTheDocument();
  });

  test('localStorage mock works', () => {
    // Clear any existing data first
    localStorage.clear();
    
    localStorage.setItem('test', 'value');
    const result = localStorage.getItem('test');
    expect(result).toBe('value');
  });

  test('fetch mock works', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ message: 'test' })
    });

    const response = await fetch('/test');
    const data = await response.json();
    expect(data.message).toBe('test');
  });
});