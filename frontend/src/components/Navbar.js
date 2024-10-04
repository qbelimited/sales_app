import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { FaUser, FaSignOutAlt } from 'react-icons/fa';
import { Modal, Button, Form, Spinner } from 'react-bootstrap';
import { useUser } from '../contexts/UserContext';
import authService from '../services/authService';
import api from '../services/api';
import './Navbar.css';

const Navbar = ({ onLogout, showToast }) => {
  const { user, loading, error, lastLoginTime, lastSessionDuration } = useUser();
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [showUpdatePasswordModal, setShowUpdatePasswordModal] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');

  const handleLogout = async () => {
    try {
      await authService.logout();
      showToast('success', 'Logged out successfully.', 'Success');
      if (onLogout) onLogout();
    } catch (error) {
      console.error('Logout failed:', error);
      showToast('danger', 'Logout failed! Please try again.', 'Error');
    }
  };

  const handleUpdatePassword = async () => {
    try {
      if (!currentPassword || !newPassword) {
        showToast('warning', 'Please fill in both password fields.', 'Warning');
        return;
      }

      const storedUser = JSON.parse(localStorage.getItem('user'));
      const userId = storedUser.id;

      await api.put(`/users/${userId}/password`, {
        current_password: currentPassword,
        new_password: newPassword,
      });

      showToast('success', 'Password updated successfully!', 'Success');
      setShowUpdatePasswordModal(false);
      setCurrentPassword('');
      setNewPassword('');
    } catch (error) {
      console.error('Password update failed:', error);
      showToast('danger', 'Failed to update password! Please try again.', 'Error');
    }
  };

  return (
    <nav className="navbar">
      <div className="navbar-left">
        <NavLink to="/dashboard" className={({ isActive }) => (isActive ? 'active' : '')}>
          Dashboard
        </NavLink>
      </div>
      <div className="navbar-right">
        <div className="navbar-profile" onClick={() => setShowProfileModal(true)}>
          <FaUser />
          <span>Profile</span>
        </div>
        <button onClick={handleLogout} className="logout-button">
          <FaSignOutAlt />
          <span>Log Out</span>
        </button>
      </div>

      {/* Profile Modal */}
      <Modal show={showProfileModal} onHide={() => setShowProfileModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Profile Details</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {loading ? (
            <Spinner animation="border" />
          ) : error ? (
            <p className="text-danger">{error}</p>
          ) : user ? (
            <>
              <p><strong>Name:</strong> {user.name || 'N/A'}</p>
              <p><strong>Email:</strong> {user.email || 'N/A'}</p>
              <p><strong>Role:</strong> {user.role?.name || 'No Role'}</p>
              <p><strong>Last Login Time:</strong> {lastLoginTime ? lastLoginTime.toLocaleString() : 'N/A'}</p>
              <p><strong>Last Session Duration:</strong> {lastSessionDuration ? `${Math.floor(lastSessionDuration / 60000)} minutes` : 'N/A'}</p>
              <p>
                <strong>Branches:</strong>
                {user.branches && user.branches.length > 0 ? (
                  user.branches.map(branch => branch.name).join(', ')
                ) : (
                  'No branches assigned'
                )}
              </p>
              <Button variant="primary" onClick={() => setShowUpdatePasswordModal(true)}>Update Password</Button>
            </>
          ) : (
            <p>User data not available</p>
          )}
        </Modal.Body>
      </Modal>

      {/* Update Password Modal */}
      <Modal show={showUpdatePasswordModal} onHide={() => setShowUpdatePasswordModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Update Password</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group>
              <Form.Label>Current Password</Form.Label>
              <Form.Control
                type="password"
                placeholder="Enter current password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
              />
            </Form.Group>
            <Form.Group>
              <Form.Label>New Password</Form.Label>
              <Form.Control
                type="password"
                placeholder="Enter new password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </Form.Group>
            <Button variant="primary" onClick={handleUpdatePassword} className="mt-3">
              Update Password
            </Button>
          </Form>
        </Modal.Body>
      </Modal>
    </nav>
  );
};

export default Navbar;
