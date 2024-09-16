import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { FaUser, FaSignOutAlt } from 'react-icons/fa';
import { Modal, Button, Form } from 'react-bootstrap';
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

        // Fetch all user sessions to get last login and session duration
        const sessionResponse = await api.get(`/users/sessions?sort_by=user_id&filter_by=&per_page=100000&page=1`);
        const sessions = sessionResponse.data.sessions;

        // Manually loop through the sessions and select those matching the userId
        const userSessions = [];
        for (let session of sessions) {
          if (session.user_id === userId) {
            userSessions.push(session);
          }
        }

        calculateLastLoginAndDuration(userSessions);

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
      if (lastSession && lastSession.login_time) {
        const lastLogin = new Date(lastSession.login_time);
        if (!isNaN(lastLogin.getTime())) {
          setLastLoginTime(lastLogin);
        } else {
          setLastLoginTime(null);
        }
      } else {
        setLastLoginTime(null);
      }

      // Get the second most recent session for the last session duration
      if (sortedSessions.length > 1) {
        const previousSession = sortedSessions[1];
        if (previousSession && previousSession.logout_time) {
          const logoutTime = new Date(previousSession.logout_time);
          const loginTime = new Date(previousSession.login_time);
          if (!isNaN(logoutTime.getTime()) && !isNaN(loginTime.getTime())) {
            const duration = logoutTime - loginTime;
            setLastSessionDuration(duration);
          } else {
            setLastSessionDuration(null);
          }
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
      if (onLogout) onLogout();
    } catch (error) {
      console.error('Logout failed:', error);
      showToast('danger', 'Logout failed! Please try again.', 'Error');
    }
  };

  // Function to handle password update
  const handleUpdatePassword = async () => {
    try {
      const storedUser = JSON.parse(localStorage.getItem('user'));
      const userId = storedUser.id;

      await api.put(`/users/${userId}/password`, {
        current_password: currentPassword,
        new_password: newPassword,
      });

      showToast('success', 'Password updated successfully!', 'Success');
      setShowUpdatePasswordModal(false);
      setShowProfileModal(false);
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
          {loading && <p>Loading...</p>}
          {error && <p className="text-danger">{error}</p>}
          {user && (
            <>
              <p><strong>Name:</strong> {user.name || 'N/A'}</p>
              <p><strong>Email:</strong> {user.email || 'N/A'}</p>
              <p><strong>Role:</strong> {user.role?.name || 'No Role'}</p>
              <p><strong>Last Login Time:</strong> {lastLoginTime ? lastLoginTime.toLocaleString() : 'N/A'}</p>
              <p><strong>Last Session Duration:</strong> {lastSessionDuration ? `${Math.floor(lastSessionDuration / 60000)} minutes` : 'N/A'}</p>
              <p><strong>Branches:</strong> {user.branches ? user.branches.join(', ') : 'N/A'}</p>
              <Button variant="primary" onClick={() => setShowUpdatePasswordModal(true)}>Update Password</Button>
            </>
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
