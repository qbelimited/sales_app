import React, { useState, useEffect } from 'react';
import api from '../services/api';
import SessionTable from '../components/SessionTable';
import { toast } from 'react-toastify';

const ManageSessionsPage = () => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSessions();
  }, []);

  // Fetch all user sessions
  const fetchSessions = async () => {
    try {
      const response = await api.get('/user/sessions'); // Adjust the endpoint if needed
      setSessions(response.data.sessions); // Use sessions array from the response
      setLoading(false);
    } catch (error) {
      console.error('Error fetching sessions:', error);
      toast.error('Failed to fetch user sessions.');
    }
  };

  // Handler to end a session
  const handleEndSession = async (sessionId, userId) => {
    try {
      await api.delete(`/user/${userId}/sessions/${sessionId}`);
      toast.success('Session ended successfully.');
      fetchSessions(); // Refresh session list
    } catch (error) {
      console.error('Error ending session:', error);
      toast.error('Failed to end the session.');
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
