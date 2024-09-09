// src/components/Toaster.js
import React from 'react';
import { Toast, ToastContainer } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimesCircle, faCheckCircle, faExclamationTriangle, faClock } from '@fortawesome/free-solid-svg-icons';
import moment from 'moment';

const Toaster = ({ toasts, removeToast }) => {
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

  const renderToast = (toast) => {
    const timePassed = moment().diff(toast.time, 'seconds');
    const timeString = `${timePassed} seconds ago`;

    return (
      <Toast
        key={toast.id}
        className="mb-3"
        onClose={() => removeToast(toast.id)}
        autohide
        delay={5000}
      >
        <Toast.Header className={`bg-${toast.variant} text-white`}>
          {renderIcon(toast.variant)} &nbsp;
          <strong className="me-auto">{toast.heading}</strong>
        </Toast.Header>
        <Toast.Body className="bg-white text-dark">
          {toast.message}
          <div className="mt-3 text-dark p-1 d-flex justify-content-end align-items-center">
            <FontAwesomeIcon icon={faClock} /> &nbsp;
            <small>{timeString}</small>
          </div>
        </Toast.Body>
      </Toast>
    );
  };

  return (
    <ToastContainer position="top-end" className="p-3" style={{ zIndex: 1050 }}>
      {toasts.map(renderToast)}
    </ToastContainer>
  );
};

export default Toaster;
