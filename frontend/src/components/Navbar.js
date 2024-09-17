import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { FaUser, FaSignOutAlt } from 'react-icons/fa';
import { Modal, Button, Form, Spinner } from 'react-bootstrap';
import authService from '../services/authService';
import api from '../services/api';
import './Navbar.css';

const Navbar = ({ onLogout, showToast }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [showUpdatePasswordModal, setShowUpdatePasswordModal] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [lastLoginTime, setLastLoginTime] = useState(null);
  const [lastSessionDuration, setLastSessionDuration] = useState(null);

  useEffect(() => {
    const fetchUserAndSessions = async () => {
      try {
        const storedUser = JSON.parse(localStorage.getItem('user'));
        if (!storedUser || !storedUser.id) {
          throw new Error('User not found in local storage');
        }
        const userId = storedUser.id;

        // Fetch user data using the userId
        const userResponse = await api.get(`/users/${userId}`);
        setUser(userResponse.data);

        // Fetch user sessions with filtering
        const sessionResponse = await api.get(`/users/sessions?user_id=${userId}&per_page=100000`);
        const sessions = sessionResponse.data.sessions || [];

        calculateLastLoginAndDuration(sessions);
      } catch (err) {
        console.error('Failed to fetch user or sessions:', err);
        setError('Failed to load user data.');
        showToast('danger', 'Failed to load user data.', 'Error');
      } finally {
        setLoading(false);
      }
    };

    fetchUserAndSessions();
  }, [showToast]);

  const calculateLastLoginAndDuration = (sessions) => {
    if (sessions.length > 0) {
      // Sort sessions by login_time in descending order
      const sortedSessions = [...sessions].sort((a, b) => new Date(b.login_time) - new Date(a.login_time));

      // Get the most recent session for the last login time
      const lastSession = sortedSessions[0];
      if (lastSession?.login_time) {
        setLastLoginTime(new Date(lastSession.login_time));
      } else {
        setLastLoginTime(null);
      }

      // Get the second most recent session for the last session duration
      if (sortedSessions.length > 1) {
        const previousSession = sortedSessions[1];
        if (previousSession?.login_time && previousSession?.logout_time) {
          const duration = new Date(previousSession.logout_time) - new Date(previousSession.login_time);
          setLastSessionDuration(duration);
        } else {
          setLastSessionDuration(null);
        }
      } else {
        setLastSessionDuration(null);
      }
    } else {
      setLastLoginTime(null);
      setLastSessionDuration(null);
    }
  };

  // Function to handle logout
  const handleLogout = async () => {
    try {
      await authService.logout();
      showToast('success', 'Logged out successfully.', 'Success'); // Show success toast on logout
      if (onLogout) onLogout();
    } catch (error) {
      console.error('Logout failed:', error);
      showToast('danger', 'Logout failed! Please try again.', 'Error');
    }
  };

  // Function to handle password update
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
      setShowProfileModal(false);
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
        {/* Add more links if needed */}
      </div>
      <div className="navbar-right">
        <div className="navbar-profile" onClick={() => setShowProfileModal(true)}>
          <FaUser />
          <span>Profile</span>
        </div>
        <button onClick={handleLogout} className="logout-button">
          <FaSignOutAlt />
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
              <p><strong>Branches:</strong> {user.branches?.length > 0 ? user.branches.map(branch => branch.name).join(', ') : 'N/A'}</p>
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
