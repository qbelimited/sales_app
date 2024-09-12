import React, { useEffect, useState } from 'react';
import userService from '../services/userService';

function AdminPage() {
  const [users, setUsers] = useState([]);

  useEffect(() => {
    userService.getUsers()
      .then(response => setUsers(response.data))
      .catch(error => console.error('Error fetching users:', error));
  }, []);

  return (
    <div className="container mt-5">
      <h1 className="mb-4">Admin Dashboard</h1>
      <div className="row">
        <div className="col-md-8">
          <h2>Users</h2>
          <ul className="list-group">
            {users.map(user => (
              <li key={user.id} className="list-group-item">
                {user.name} ({user.email})
              </li>
            ))}
          </ul>
        </div>
        <div className="col-md-4">
          <h2>Actions</h2>
          <button className="btn btn-primary mb-2">Add User</button>
          <button className="btn btn-secondary">View Reports</button>
        </div>
      </div>
    </div>
  );
}

export default AdminPage;
