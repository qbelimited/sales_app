import React, { useState } from 'react';

const SessionTable = ({ sessions, loading, onEndSession }) => {
  const [viewAllSessionsForUser, setViewAllSessionsForUser] = useState(null);

  if (loading) {
    return <p>Loading sessions...</p>;
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
  const filterSessionsForUser = (userId) => {
    return sessions.filter(session => session.user_id === userId);
  };

  // Calculate session duration
  const calculateSessionDuration = (loginTime, logoutTime) => {
    if (logoutTime) {
      const duration = new Date(logoutTime) - new Date(loginTime);
      return `${Math.floor(duration / 60000)} minutes`;
    }
    return 'Active';
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
          <table className="table table-striped">
            <thead>
              <tr>
                <th>Session ID</th>
                <th>User Name</th>
                <th>Login Time</th>
                <th>Logout Time</th>
                <th>Session Duration</th> {/* Added column for session duration */}
                <th>IP Address</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filterSessionsForUser(viewAllSessionsForUser).length > 0 ? (
                filterSessionsForUser(viewAllSessionsForUser).map((session) => (
                  <tr key={session.id}>
                    <td>{session.id}</td>
                    <td>{session.user_name}</td>
                    <td>{new Date(session.login_time).toLocaleString()}</td>
                    <td>{session.logout_time ? new Date(session.logout_time).toLocaleString() : 'Active'}</td>
                    <td>{calculateSessionDuration(session.login_time, session.logout_time)}</td> {/* Display session duration */}
                    <td>{session.ip_address}</td>
                    <td>{session.is_active ? 'Active' : 'Inactive'}</td>
                    <td>
                      {session.is_active && (
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => onEndSession(session.id, session.user_id)} // Pass session ID and user ID
                        >
                          End Session
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="8">No active sessions found for this user.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      ) : (
        <table className="table table-striped">
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
                <tr key={user.user_id}>
                  <td>{user.user_name}</td>
                  <td>{sessions.filter(session => session.user_id === user.user_id && session.is_active).length}</td>
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
    </div>
  );
};

export default SessionTable;
