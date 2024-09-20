// components/ErrorBoundary.js
import React from 'react';
import { Button } from 'react-bootstrap';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error", error, errorInfo);
    // You might want to log the error to an error reporting service
  }

  handleReload = () => {
    window.location.reload(); // Reload the page
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={styles.errorContainer}>
          <h1 style={styles.errorTitle}>Something Went Wrong</h1>
          <p style={styles.errorMessage}>
            An unexpected error has occurred. Please try reloading the page or contact support.
          </p>
          <Button variant="primary" onClick={this.handleReload}>
            Reload Page
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Styles for the error boundary
const styles = {
  errorContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100vh',
    textAlign: 'center',
    backgroundColor: '#f8d7da', // Light red background
    color: '#721c24', // Dark red text
    padding: '20px',
    borderRadius: '5px',
  },
  errorTitle: {
    fontSize: '2rem',
    marginBottom: '10px',
  },
  errorMessage: {
    marginBottom: '20px',
    fontSize: '1.2rem',
  },
};

export default ErrorBoundary;
