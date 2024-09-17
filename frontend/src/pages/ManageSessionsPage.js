import React, { useState, useEffect, useCallback } from 'react'; // Import useState along with other hooks
import { useAuth } from '../contexts/AuthContext'; // Import useAuth for global state
import api from '../services/api';
import SessionTable from '../components/SessionTable';

const ManageSessionsPage = ({ showToast }) => {
  const { state } = useAuth(); // Use global state from context
  const { user } = state; // Extract user from the state
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch all user sessions
  const fetchSessions = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get('/users/sessions'); // Adjust the endpoint if needed
      setSessions(response.data.sessions || []); // Use sessions array from the response
    } catch (error) {
      console.error('Error fetching sessions:', error);
      showToast('danger', 'Failed to fetch user sessions.', 'Error');
    } finally {
      setLoading(false);
    }
  }, [showToast]); // Add showToast to the dependency array

  useEffect(() => {
    if (user) {
      fetchSessions(); // Fetch sessions only if user is authenticated
    }
  }, [fetchSessions, user]); // Include fetchSessions and user in the dependency array

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
