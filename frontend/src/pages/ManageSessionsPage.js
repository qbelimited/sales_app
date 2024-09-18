import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import SessionTable from '../components/SessionTable';
import Loading from '../components/Loading';
import { useUser } from '../contexts/UserContext'; // Import the UserContext

const ManageSessionsPage = ({ showToast }) => {
  const { user, sessions, loading, error } = useUser(); // Access user and sessions from context
  const [loadingSessions, setLoadingSessions] = useState(true); // Local loading state for sessions

  // Fetch all user sessions
  const fetchSessions = useCallback(async () => {
    setLoadingSessions(true);
    const timeoutId = setTimeout(() => {
      showToast('warning', 'Fetching sessions is taking longer than expected.', 'Warning');
    }, 5000);

    try {
      // const response = await api.get('/users/sessions');
      // You can also update the context here if you want
      // setSessions(response.data.sessions || []);
      // console.log('Sessions fetched:', response.data.sessions);
    } catch (error) {
      console.error('Error fetching sessions:', error);
      showToast('danger', 'Failed to fetch user sessions.', 'Error');
    } finally {
      setLoadingSessions(false);
      clearTimeout(timeoutId);
    }
  }, [showToast]);

  useEffect(() => {
    if (user) {
      fetchSessions();
    }
  }, [fetchSessions, user]);

  // Handler to end a session
  const handleEndSession = async (sessionId, userId) => {
    try {
      await api.delete(`/users/${userId}/sessions/${sessionId}`);
      showToast('success', 'Session ended successfully.', 'Success');
      fetchSessions(); // Refresh session list
    } catch (error) {
      console.error('Error ending session:', error);
      showToast('danger', 'Failed to end the session.', 'Error');
    }
  };

  return (
    <div className="container mt-5">
      <h1 className="text-center mb-4">Manage User Sessions</h1>
      {loadingSessions || loading ? <Loading /> : (
        <SessionTable
          sessions={sessions}
          loading={loadingSessions}
          onEndSession={handleEndSession}
        />
      )}
      {error && <p className="text-danger">{error}</p>} {/* Display error if any */}
    </div>
  );
};

export default ManageSessionsPage;
