import React, { useState } from 'react';
import { useUser } from '../contexts/UserContext';
import { Modal, Button } from 'react-bootstrap';

const SessionTable = ({ showToast, onEndSession }) => {
  const { sessions, loading, error } = useUser(); // Access sessions from UserContext
  const [viewAllSessionsForUser, setViewAllSessionsForUser] = useState(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState(null);
  const [visibleInactiveSessions, setVisibleInactiveSessions] = useState({}); // Track which user's inactive sessions are visible

  if (loading) {
    return <p aria-live="polite">Loading sessions...</p>;
  }

  if (error) {
    return <p className="text-danger" role="alert">Failed to load sessions.</p>;
  }

  // Get unique users from sessions
  const uniqueUsers = Array.from(new Set(sessions.map(session => session.user_id)))
    .map(userId => {
      return sessions.find(session => session.user_id === userId);
    })
    .sort((a, b) => {
      // Sort by active session count descending
      const aActiveCount = sessions.filter(session => session.user_id === a.user_id && session.is_active).length;
      const bActiveCount = sessions.filter(session => session.user_id === b.user_id && session.is_active).length;
      return bActiveCount - aActiveCount;
    });

  // Filter sessions for a specific user
  const filterSessionsForUser = (userId, isActive = true) => {
    return sessions.filter(session => session.user_id === userId && session.is_active === isActive);
  };

  // Calculate session duration
  const calculateSessionDuration = (loginTime, logoutTime) => {
    if (logoutTime) {
      const duration = (new Date(logoutTime) - new Date(loginTime)) / 1000; // duration in seconds
      const hours = Math.floor(duration / 3600);
      const minutes = Math.floor((duration % 3600) / 60);
      const seconds = Math.floor(duration % 60);
      return `${hours} hours, ${minutes} minutes, ${seconds} seconds`;
    }
    return 'Active';
  };

  const handleDeleteSession = (sessionId, userId) => {
    setSessionToDelete({ sessionId, userId });
    setShowConfirmModal(true);
  };

  const confirmDeleteSession = async () => {
    if (sessionToDelete) {
      await onEndSession(sessionToDelete.sessionId, sessionToDelete.userId);
      showToast('success', 'Session ended successfully.', 'Success'); // Show success toast after deletion
      setShowConfirmModal(false);
      setSessionToDelete(null);
    }
  };

  const toggleInactiveSessions = (userId) => {
    setVisibleInactiveSessions(prevState => ({
      ...prevState,
      [userId]: !prevState[userId]
    }));
  };

  return (
    <div>
      {viewAllSessionsForUser ? (
        <div>
          <button
            className="btn btn-secondary mb-3"
            onClick={() => setViewAllSessionsForUser(null)}
          >
            Back to All Users
          </button>
          <table className="table table-striped" role="table">
            <thead>
              <tr>
                <th>Session ID</th>
                <th>User Name</th>
                <th>Login Time</th>
                <th>Logout Time</th>
                <th>Session Duration</th>
                <th>IP Address</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filterSessionsForUser(viewAllSessionsForUser).map((session) => (
                <tr key={session.id} role="row">
                  <td>{session.id}</td>
                  <td>{session.user_name}</td>
                  <td>{new Date(session.login_time).toLocaleString()}</td>
                  <td>{session.logout_time ? new Date(session.logout_time).toLocaleString() : 'Active'}</td>
                  <td>{calculateSessionDuration(session.login_time, session.logout_time)}</td>
                  <td>{session.ip_address}</td>
                  <td>{session.is_active ? 'Active' : 'Inactive'}</td>
                  <td>
                    {session.is_active && (
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => handleDeleteSession(session.id, session.user_id)} // Trigger delete confirmation
                      >
                        End Session
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {/* Render Inactive Sessions */}
              {visibleInactiveSessions[viewAllSessionsForUser] && (
                filterSessionsForUser(viewAllSessionsForUser, false).map((session) => (
                  <tr key={session.id} className="table-secondary" role="row">
                    <td>{session.id}</td>
                    <td>{session.user_name}</td>
                    <td>{new Date(session.login_time).toLocaleString()}</td>
                    <td>{session.logout_time ? new Date(session.logout_time).toLocaleString() : 'Active'}</td>
                    <td>{calculateSessionDuration(session.login_time, session.logout_time)}</td>
                    <td>{session.ip_address}</td>
                    <td>{session.is_active ? 'Active' : 'Inactive'}</td>
                    <td>N/A</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          <button
            className="btn btn-info btn-sm"
            onClick={() => toggleInactiveSessions(viewAllSessionsForUser)}
          >
            {visibleInactiveSessions[viewAllSessionsForUser] ? 'Hide Inactive Sessions' : 'Show Inactive Sessions'}
          </button>
        </div>
      ) : (
        <table className="table table-striped" role="table">
          <thead>
            <tr>
              <th>User Name</th>
              <th>Active Sessions Count</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {uniqueUsers.length > 0 ? (
              uniqueUsers.map(user => (
                <tr key={user.user_id} role="row">
                  <td>{user.user_name}</td>
                  <td>{filterSessionsForUser(user.user_id).length}</td>
                  <td>
                    <button
                      className="btn btn-info btn-sm"
                      onClick={() => setViewAllSessionsForUser(user.user_id)}
                    >
                      View All Sessions
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="3">No users with active sessions found.</td>
              </tr>
            )}
          </tbody>
        </table>
      )}

      {/* Confirmation Modal */}
      <Modal show={showConfirmModal} onHide={() => setShowConfirmModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Deletion</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>Are you sure you want to end this session? This action cannot be undone.</p>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowConfirmModal(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={confirmDeleteSession}>
            End Session
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default SessionTable;
