import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

function Navbar({ onLogout }) {
  const navigate = useNavigate();

  // Function to handle the logout process
  const handleLogout = async () => {
    const token = localStorage.getItem('authToken');  // Retrieve the token from localStorage

    try {
      // Send the logout request with the Authorization header
      await axios.post('http://127.0.0.1:5000/api/v1/auth/logout', {}, {
        headers: {
          'Authorization': `Bearer ${token}`,  // Add the Authorization header with the JWT token
          'Accept': 'application/json',
        },
      });

      // Clear the token from localStorage
      localStorage.removeItem('authToken');

      // Call the onLogout function to clear session and user role
      onLogout();

      // Redirect to the login page
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
      <div className="container-fluid">
        <Link className="navbar-brand" to="/">SalesApp</Link>
        <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
          <span className="navbar-toggler-icon"></span>
        </button>
        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav ms-auto">
            {/* Profile link */}
            <li className="nav-item">
              <Link className="nav-link" to="/profile">Profile</Link>
            </li>
            {/* Logout button */}
            <li className="nav-item">
              <button className="btn btn-link nav-link" onClick={handleLogout}>Logout</button>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
