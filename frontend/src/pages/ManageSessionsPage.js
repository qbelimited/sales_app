import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import SessionTable from '../components/SessionTable';
import Loading from '../components/Loading';

const ManageSessionsPage = ({ showToast }) => {
  const [sessions, setSessions] = useState([]); // Local state for sessions
  const [loadingSessions, setLoadingSessions] = useState(true); // Local loading state
  const [error, setError] = useState(null);

  // Fetch all user sessions
  const fetchSessions = useCallback(async () => {
    setLoadingSessions(true);
    setError(null); // Reset error before fetching
    const timeoutId = setTimeout(() => {
      showToast('warning', 'Fetching sessions is taking longer than expected.', 'Warning');
    }, 5000);

    try {
      const response = await api.get('/users/sessions');
      setSessions(response.data.sessions);
    } catch (error) {
      console.error('Error fetching sessions:', error);
      setError('Failed to fetch user sessions.');
      showToast('danger', 'Failed to fetch user sessions.', 'Error');
    } finally {
      setLoadingSessions(false);
      clearTimeout(timeoutId);
    }
  }, [showToast]);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

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
    <div className="container mt-5" role="main">
      <h1 className="text-center mb-4" aria-live="polite">Manage User Sessions</h1>
      {loadingSessions ? (
        <Loading />
      ) : sessions.length > 0 ? (
        <SessionTable
          sessions={sessions}
          onEndSession={handleEndSession}
          showToast={showToast}
        />
      ) : (
        <p className="text-center" aria-live="polite">No active sessions available.</p> // Feedback for empty session list
      )}
      {error && <p className="text-danger" role="alert">{error}</p>} {/* Display error message */}
    </div>
  );
};

export default ManageSessionsPage;
