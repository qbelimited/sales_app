import React from 'react';
import { Toast, ToastContainer } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimesCircle, faCheckCircle, faExclamationTriangle, faClock } from '@fortawesome/free-solid-svg-icons';
import moment from 'moment';

const Toaster = ({ toasts, removeToast, autohideDelay = 5000 }) => {
  // Helper function to render the appropriate icon based on the toast variant
  const renderIcon = (variant) => {
    switch (variant) {
      case 'danger':
        return <FontAwesomeIcon icon={faTimesCircle} />;
      case 'success':
        return <FontAwesomeIcon icon={faCheckCircle} />;
      case 'warning':
        return <FontAwesomeIcon icon={faExclamationTriangle} />;
      default:
        return null;
    }
  };

  // Helper function to render each toast
  const renderToast = (toast) => {
    return (
      <Toast
        key={toast.id}  // Unique key for each toast
        className={`mb-3 fade`}  // Add a fade animation class
        onClose={() => removeToast(toast.id)}  // Handle close
        autohide
        delay={autohideDelay}  // Autohide after a configurable delay
        aria-live="assertive"  // Accessibility: Ensure toasts are read immediately
      >
        <Toast.Header className={`bg-${toast.variant} text-white`}>
          {renderIcon(toast.variant)} &nbsp;
          <strong className="me-auto">{toast.heading}</strong>
        </Toast.Header>
        <Toast.Body className="bg-white text-dark">
          {toast.message}
          <div className="mt-3 text-dark p-1 d-flex justify-content-end align-items-center">
            <FontAwesomeIcon icon={faClock} /> &nbsp;
            <small>{moment(toast.time).fromNow()}</small>  {/* Display time passed in a friendly format */}
          </div>
        </Toast.Body>
      </Toast>
    );
  };

  return (
    <ToastContainer position="top-end" className="p-3" style={{ zIndex: 1050 }}>
      {toasts.length > 0 && toasts.map((toast) => renderToast(toast))} {/* Render toasts if available */}
    </ToastContainer>
  );
};

export default Toaster;
