import React from 'react';
import { NavLink } from 'react-router-dom';
import { FaUser, FaSignOutAlt } from 'react-icons/fa';
import { toast } from 'react-toastify'; // Import toast
import authService from '../services/authService'; // Assuming you have authService for logout
import 'react-toastify/dist/ReactToastify.css'; // Import Toastify CSS
import './Navbar.css'; // Ensure this file exists for styling

const Navbar = ({ onLogout }) => {
  // Function to handle logout
  const handleLogout = async () => {
    try {
      await authService.logout(); // Call the logout function from authService
      toast.success('Logged out successfully!'); // Show success toast
      if (onLogout) onLogout(); // Optionally call a passed prop function to handle further actions
      window.location.href = '/login'; // Redirect to login page after logout
    } catch (error) {
      console.error('Logout failed:', error);
      toast.error('Logout failed! Please try again.'); // Show error toast
    }
  };

  return (
    <nav className="navbar">
      <div className="navbar-left">
        <NavLink to="/dashboard" className={({ isActive }) => (isActive ? 'active' : '')}>
          Dashboard
        </NavLink>
        {/* Add more links if needed */}
      </div>
      <div className="navbar-right">
        <div className="navbar-profile">
          <FaUser />
          <span>Profile</span>
        </div>
        <button onClick={handleLogout} className="logout-button">
          <FaSignOutAlt />
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
