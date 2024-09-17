import React from 'react';
import TableWithPagination from '../components/TableWithPagination';

const ManageUsersPage = ({ showToast }) => {
  // Columns definition for the users table
  const userColumns = [
    { Header: 'Name', accessor: 'name' },
    { Header: 'Email', accessor: 'email' },
    {
      Header: 'Role',
      accessor: (row) => (row.role && row.role.name ? row.role.name : 'No Role'),
    },
    {
      Header: 'Created At',
      accessor: (row) => new Date(row.created_at).toLocaleDateString(),
    },
  ];

  return (
    <div className="container mt-5">
      <h1 className="text-center mb-4">Manage Users</h1>

      {/* TableWithPagination component for users table */}
      <TableWithPagination
        endpoint="/users/" // API endpoint to fetch users
        columns={userColumns} // Columns to display in the table
        title="Users List" // Title for the table
        showToast={showToast} // Pass showToast to the component
      />
    </div>
  );
};

export default ManageUsersPage;
