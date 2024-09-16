import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import SessionTable from '../components/SessionTable';

const ManageSessionsPage = ({ showToast }) => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch all user sessions
  const fetchSessions = useCallback(async () => {
    try {
      const response = await api.get('/users/sessions'); // Adjust the endpoint if needed
      setSessions(response.data.sessions); // Use sessions array from the response
      setLoading(false);
    } catch (error) {
      console.error('Error fetching sessions:', error);
      showToast('danger', 'Failed to fetch user sessions.', 'Error');
    }
  }, [showToast]); // Add showToast to the dependency array

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]); // Include fetchSessions in the dependency array

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
      <SessionTable
        sessions={sessions}
        loading={loading}
        onEndSession={handleEndSession}
      />
    </div>
  );
};

export default ManageSessionsPage;
