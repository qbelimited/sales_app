import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import SessionTable from '../components/SessionTable';

const ManageSessionsPage = ({ showToast, user }) => { // Accept user as a prop
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch all user sessions
  const fetchSessions = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get('/users/sessions');
      setSessions(response.data.sessions || []);
    } catch (error) {
      console.error('Error fetching sessions:', error);
      showToast('danger', 'Failed to fetch user sessions.', 'Error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    if (user) { // Check if user is passed as a prop
      fetchSessions();
    }
  }, [fetchSessions, user]);

  // Handler to end a session
  const handleEndSession = async (sessionId, userId) => {
    try {
      await api.delete(`/users/${userId}/sessions/${sessionId}`);
      showToast('success', 'Session ended successfully.', 'Success');
      fetchSessions();
    } catch (error) {
      console.error('Error ending session:', error);
      showToast('danger', 'Failed to end the session.', 'Error');
    }
  };

  return (
    <div className="container mt-5">
      <h1 className="text-center mb-4">Manage User Sessions</h1>
      <SessionTable
        sessions={sessions}
        loading={loading}
        onEndSession={handleEndSession}
      />
    </div>
  );
};

export default ManageSessionsPage;
