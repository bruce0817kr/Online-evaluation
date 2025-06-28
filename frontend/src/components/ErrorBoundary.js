import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null 
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error to console and potentially to error reporting service
    console.error('Error caught by boundary:', error, errorInfo);
    
    this.setState({
      error: error,
      errorInfo: errorInfo
    });

    // You can also log the error to an error reporting service here
    // logErrorToService(error, errorInfo);
  }

  handleRefresh = () => {
    // Reset the error boundary state
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null 
    });
    
    // Optionally reload the page
    if (this.props.fallbackComponent) {
      // Just reset state if using custom fallback
      return;
    }
    
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback component if provided
      if (this.props.fallbackComponent) {
        return this.props.fallbackComponent(this.state.error, this.handleRefresh);
      }

      // Default error UI
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
            <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full mb-4">
              <svg 
                className="w-6 h-6 text-red-600" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
                />
              </svg>
            </div>
            
            <div className="text-center">
              <h1 className="text-lg font-semibold text-gray-900 mb-2">
                애플리케이션 오류
              </h1>
              <p className="text-sm text-gray-600 mb-4">
                예상치 못한 오류가 발생했습니다. 
                잠시 후 다시 시도해주세요.
              </p>
              
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="text-left mb-4 bg-gray-50 p-3 rounded text-xs">
                  <summary className="cursor-pointer font-medium text-gray-700 mb-2">
                    개발자 정보 (개발 모드에서만 표시)
                  </summary>
                  <div className="text-red-600 mb-2">
                    <strong>Error:</strong> {this.state.error.toString()}
                  </div>
                  {this.state.errorInfo && (
                    <div className="text-gray-600">
                      <strong>Component Stack:</strong>
                      <pre className="whitespace-pre-wrap text-xs mt-1">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    </div>
                  )}
                </details>
              )}
              
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  onClick={this.handleRefresh}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  새로고침
                </button>
                <button
                  onClick={() => window.location.href = '/'}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
                >
                  홈으로 이동
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Higher-order component for easier usage
export const withErrorBoundary = (Component, fallbackComponent) => {
  return function WrappedComponent(props) {
    return (
      <ErrorBoundary fallbackComponent={fallbackComponent}>
        <Component {...props} />
      </ErrorBoundary>
    );
  };
};

// Hook for functional components to handle errors
export const useErrorHandler = () => {
  const [error, setError] = React.useState(null);
  
  const resetError = React.useCallback(() => {
    setError(null);
  }, []);
  
  const captureError = React.useCallback((error) => {
    console.error('Error captured by hook:', error);
    setError(error);
  }, []);
  
  // Throw error to be caught by ErrorBoundary
  if (error) {
    throw error;
  }
  
  return { captureError, resetError };
};

// Simple error display component for non-critical errors
export const ErrorMessage = ({ 
  error, 
  onRetry, 
  onDismiss, 
  className = '',
  showDetails = false 
}) => {
  const errorMessage = error?.userMessage || error?.message || '알 수 없는 오류가 발생했습니다.';
  
  return (
    <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg 
            className="h-5 w-5 text-red-400" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
            />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-800">
            오류가 발생했습니다
          </h3>
          <div className="mt-1 text-sm text-red-700">
            {errorMessage}
          </div>
          
          {showDetails && error?.response?.data && (
            <details className="mt-2">
              <summary className="cursor-pointer text-xs text-red-600">
                자세한 정보
              </summary>
              <pre className="mt-1 text-xs text-red-600 bg-red-100 p-2 rounded overflow-auto">
                {JSON.stringify(error.response.data, null, 2)}
              </pre>
            </details>
          )}
          
          <div className="mt-3 flex space-x-3">
            {onRetry && (
              <button
                onClick={onRetry}
                className="text-sm bg-red-100 text-red-800 px-3 py-1 rounded-md hover:bg-red-200 transition-colors"
              >
                다시 시도
              </button>
            )}
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="text-sm text-red-600 hover:text-red-800 transition-colors"
              >
                닫기
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ErrorBoundary;