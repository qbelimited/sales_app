import React from 'react';
import TableWithPagination from '../components/TableWithPagination';

const ManageUsersPage = () => {
  // Columns definition for the users table
  const userColumns = [
    { Header: 'Name', accessor: 'name' },
    { Header: 'Email', accessor: 'email' },
    { Header: 'Role', accessor: 'role.name' },  // Adjust according to your backend field
    { Header: 'Created At', accessor: 'created_at' }  // Assuming there's a creation date field
  ];

  return (
    <div className="container mt-5">
      <h1 className="text-center mb-4">Manage Users</h1>

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
