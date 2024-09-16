// LoadingSpinner.js
import React from 'react';
import './LoadingSpinner.css'; // Add your styles

const LoadingSpinner = () => (
  <div className="loading-spinner">
    <div className="spinner-border" role="status">
      <span className="sr-only">Loading...</span>
    </div>
  </div>
);

export default LoadingSpinner;
