import React, { useCallback } from 'react';
import { Toast, ToastContainer, Button } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimesCircle, faCheckCircle, faExclamationTriangle, faInfoCircle, faClock, faCloudDownloadAlt } from '@fortawesome/free-solid-svg-icons';
import moment from 'moment';

const Toaster = React.memo(({ toasts, removeToast, updateServiceWorker, autohideDelay = 5000 }) => {
  // Helper function to render the appropriate icon based on the toast variant
  const renderIcon = (variant) => {
    const iconMap = {
      danger: faTimesCircle,
      success: faCheckCircle,
      warning: faExclamationTriangle,
      update: faCloudDownloadAlt,
      default: faInfoCircle,
    };
    return <FontAwesomeIcon icon={iconMap[variant] || iconMap.default} />;
  };

  // Helper function to render each toast
  const renderToast = useCallback((toast) => {
    return (
      <Toast
        key={toast.id}
        className="mb-3 fade"
        onClose={() => removeToast(toast.id)}
        autohide={toast.variant !== 'update'}
        delay={autohideDelay}
        aria-live="assertive"
        role="alert"
      >
        <Toast.Header className={`bg-${toast.variant} text-white`}>
          {renderIcon(toast.variant)} &nbsp;
          <strong className="me-auto">{toast.heading}</strong>
        </Toast.Header>
        <Toast.Body className="bg-white text-dark">
          {toast.message}
          <div className="mt-3 text-dark p-1 d-flex justify-content-end align-items-center">
            <FontAwesomeIcon icon={faClock} /> &nbsp;
            <small>{moment(toast.time).fromNow()}</small>
          </div>
          {toast.variant === 'update' && (
            <Button variant="primary" className="mt-2" onClick={updateServiceWorker}>
              Apply Update
            </Button>
          )}
        </Toast.Body>
      </Toast>
    );
  }, [autohideDelay, removeToast, updateServiceWorker]);

  return (
    <ToastContainer position="top-end" className="p-3" style={{ zIndex: 1050 }}>
      {toasts.map(renderToast)}
    </ToastContainer>
  );
});

export default Toaster;
