import React from 'react';
import { NavLink } from 'react-router-dom';
import { FaUser, FaSignOutAlt } from 'react-icons/fa';
import './Navbar.css'; // Ensure this file exists for styling

const Navbar = ({ onLogout }) => {
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
        <button onClick={onLogout} className="logout-button">
          <FaSignOutAlt />
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
