import React, { useState, useEffect } from 'react';
import TableWithPagination from '../components/TableWithPagination';
import { toast } from 'react-toastify';
import api from '../services/api';

const ManageUsersPage = () => {
  // State for loading, error, and users data
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Columns definition for the users table
  const userColumns = [
    { Header: 'Name', accessor: 'name' },
    { Header: 'Email', accessor: 'email' },
    {
      Header: 'Role',
      accessor: (row) => row.role && row.role.name ? row.role.name : 'No Role',
    },
    {
      Header: 'Created At',
      accessor: (row) => new Date(row.created_at).toLocaleDateString(),
    },
  ];

  useEffect(() => {
    // Fetch users data on component mount
    const fetchUsers = async () => {
      try {
        // Assuming you have a function to fetch users data
        const response = await api.get(`/users/`)
        return response.data.users;
      } catch (err) {
        console.error('Failed to fetch users:', err);
        setError('Failed to load users. Please try again later.');
        toast.error('Failed to load users.');
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, []);

  return (
    <div className="container mt-5">
      <h1 className="text-center mb-4">Manage Users</h1>

      {/* Display loading message if data is being fetched */}
      {loading && <p className="text-center">Loading...</p>}

      {/* Display error message if there's an error */}
      {error && <p className="text-center text-danger">{error}</p>}

      {/* TableWithPagination component for users table */}
      <TableWithPagination
        endpoint="/users/"  // API endpoint to fetch users
        columns={userColumns}  // Columns to display in the table
        title="Users List"  // Title for the table
      />
    </div>
  );
};

export default ManageUsersPage;
