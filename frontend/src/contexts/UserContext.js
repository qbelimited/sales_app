import React, { createContext, useState, useEffect, useContext } from 'react';
import api from '../services/api';

const UserContext = createContext();

export const UserProvider = ({ children, showToast }) => {
  const [user, setUser] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastLoginTime, setLastLoginTime] = useState(null);
  const [lastSessionDuration, setLastSessionDuration] = useState(null);

  useEffect(() => {
    const fetchUserAndSessions = async () => {
      setLoading(true);
      setError(null); // Reset error state on new fetch

      try {
        const storedUser = JSON.parse(localStorage.getItem('user'));

        // Handle missing user
        if (!storedUser || !storedUser.id) {
          showToast('danger', 'User not found in local storage', 'Error');
          return; // Prevent further execution
        }

        const userId = storedUser.id;

        // Fetch user data
        const userResponse = await api.get(`/users/${userId}`);
        if (!userResponse.data) throw new Error('User data is missing');

        setUser(userResponse.data);

        // Fetch user sessions
        const sessionResponse = await api.get(`/users/sessions?user_id=${userId}&per_page=100000`);
        const fetchedSessions = sessionResponse.data.sessions || [];
        setSessions(fetchedSessions);

        // Calculate last login time and duration
        calculateLastLoginAndDuration(fetchedSessions);
      } catch (err) {
        console.error('Failed to fetch user or sessions:', err);
        setError('Failed to load user data.');
        if (err.message !== 'User not found in local storage') {
          showToast('danger', 'Failed to load user data.', 'Error');
        }
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

  return (
    <UserContext.Provider value={{ user, sessions, loading, error, lastLoginTime, lastSessionDuration }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => {
  return useContext(UserContext);
};

export default UserContext;
