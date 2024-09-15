import React from 'react';

const SessionTable = ({ sessions, loading, onEndSession }) => {
  if (loading) {
    return <p>Loading sessions...</p>;
  }

  return (
    <table className="table table-striped">
      <thead>
        <tr>
          <th>Session ID</th>
          <th>User Name</th>
          <th>Login Time</th>
          <th>Logout Time</th>
          <th>IP Address</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {sessions.length > 0 ? (
          sessions.map((session) => (
            <tr key={session.id}>
              <td>{session.id}</td>
              <td>{session.user_name}</td> {/* Display the user's name */}
              <td>{new Date(session.login_time).toLocaleString()}</td>
              <td>{session.logout_time ? new Date(session.logout_time).toLocaleString() : 'Active'}</td>
              <td>{session.ip_address}</td>
              <td>{session.is_active ? 'Active' : 'Inactive'}</td>
              <td>
                {session.is_active && (
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => onEndSession(session.id, session.user_id)} // Correctly pass user_id here
                  >
                    End Session
                  </button>
                )}
              </td>
            </tr>
          ))
        ) : (
          <tr>
            <td colSpan="7">No sessions found.</td>
          </tr>
        )}
      </tbody>
    </table>
  );
};

export default SessionTable;
