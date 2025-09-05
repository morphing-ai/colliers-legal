// frontend/src/components/error/ErrorBoundary.tsx
import React from 'react';

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null 
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { 
      hasError: true, 
      error 
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    console.error("Uncaught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 m-4 border-2 border-red-500 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-900 dark:text-red-50">
          <h2 className="text-2xl font-bold mb-4">Something went wrong</h2>
          <details className="mt-4">
            <summary className="cursor-pointer font-medium text-red-700 dark:text-red-300 mb-2">
              View error details
            </summary>
            <div className="mt-2 p-4 bg-white dark:bg-gray-800 rounded border border-red-300 dark:border-red-800">
              <p className="mb-2 font-mono text-sm">{this.state.error?.toString()}</p>
              <p className="font-bold mt-4 mb-1">Stack trace:</p>
              <pre className="bg-gray-100 dark:bg-gray-900 p-2 rounded overflow-auto text-xs">
                {this.state.error?.stack}
              </pre>
            </div>
          </details>
          <div className="mt-6">
            <button
              className="px-4 py-2 bg-primary text-white rounded hover:bg-primary/90"
              onClick={() => window.location.href = '/'}
            >
              Return to Dashboard
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
