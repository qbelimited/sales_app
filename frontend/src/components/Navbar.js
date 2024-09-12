import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import Toaster from './Toaster';  // Assuming you have a Toaster component
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUser, faSignOutAlt, faBars } from '@fortawesome/free-solid-svg-icons';

function Navbar({ onLogout }) {
  const [toasts, setToasts] = useState([]);
  const navigate = useNavigate();

  const showToast = (variant, message, heading) => {
    const newToast = {
      id: Date.now(),
      variant,
      message,
      heading,
      time: new Date(),
    };
    setToasts((prevToasts) => [...prevToasts, newToast]);
  };

  // Function to handle the logout process
  const handleLogout = async () => {
    const token = localStorage.getItem('accessToken');  // Retrieve the token from localStorage

    try {
      // Send the logout request with the Authorization header
      await api.post('/auth/logout', {}, {
        headers: {
          'Authorization': `Bearer ${token}`,  // Add the Authorization header with the JWT token
          'Accept': 'application/json',
        },
      });

      // Clear the token and user info from localStorage
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('userRole');
      localStorage.removeItem('userID');
      localStorage.removeItem('user');

      // Call the onLogout function to clear session and user role
      onLogout();

      // Show logout success toast
      showToast('success', 'Successfully logged out!', 'Success');

      // Redirect to the login page
      navigate('/login');
    } catch (error) {
      showToast('danger', 'Logout failed!', 'Error');
      console.error('Logout failed:', error);
    }
  };

  return (
    <>
      <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
        <div className="container-fluid">
          <Link className="navbar-brand" to="/">SalesApp</Link>
          <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
            <span className="navbar-toggler-icon">
              <FontAwesomeIcon icon={faBars} />
            </span>
          </button>
          <div className="collapse navbar-collapse" id="navbarNav">
            <ul className="navbar-nav ms-auto">
              {/* Profile link */}
              <li className="nav-item">
                <Link className="nav-link" to="/profile">
                  <FontAwesomeIcon icon={faUser} /> Profile
                </Link>
              </li>
              {/* Logout button */}
              <li className="nav-item">
                <button className="btn btn-link nav-link" onClick={handleLogout}>
                  <FontAwesomeIcon icon={faSignOutAlt} /> Logout
                </button>
              </li>
            </ul>
          </div>
        </div>
      </nav>

      {/* Toaster Component to Show Toast Messages */}
      <Toaster toasts={toasts} removeToast={(id) => setToasts(toasts.filter((t) => t.id !== id))} />
    </>
  );
}

export default Navbar;
