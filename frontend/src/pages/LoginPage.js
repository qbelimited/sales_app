import React, { useState } from 'react';
import { Toast, ToastContainer } from 'react-bootstrap';

function LoginPage() {
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [toastVariant, setToastVariant] = useState(''); // This will control the color of the toast

  const handleMicrosoftLogin = async () => {
    try {
      const response = await fetch('/api/v1/auth/login');
      if (response.ok) {
        setToastMessage('Login successful!');
        setToastVariant('success');
      } else {
        setToastMessage('Login failed!');
        setToastVariant('danger');
      }
    } catch (error) {
      setToastMessage('An error occurred during login.');
      setToastVariant('danger');
    } finally {
      setShowToast(true);
    }
  };

  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-md-6">
          <h2 className="text-center mb-4">Login</h2>
          <div className="d-grid">
            <button
              onClick={handleMicrosoftLogin}
              className="btn btn-primary btn-lg">
              Sign in with Microsoft 365
            </button>
          </div>
        </div>
      </div>

      {/* Toast Notification */}
      <ToastContainer position="top-end" className="p-3">
        <Toast
          onClose={() => setShowToast(false)}
          show={showToast}
          delay={3000}
          autohide
          bg={toastVariant}  // Use variant for background color
        >
          <Toast.Header>
            <strong className="me-auto">Notification</strong>
          </Toast.Header>
          <Toast.Body>{toastMessage}</Toast.Body>
        </Toast>
      </ToastContainer>
    </div>
  );
}

export default LoginPage;
