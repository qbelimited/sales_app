import React from 'react';
import TableWithPagination from '../components/TableWithPagination';

const ManageUsersPage = () => {
  const userColumns = [
    { Header: 'Name', accessor: 'name' },
    { Header: 'Email', accessor: 'email' },
    { Header: 'Role', accessor: 'role_name' },  // Adjusted to display the role name
    { Header: 'Created At', accessor: 'created_at' },
  ];

  const sessionColumns = [
    { Header: 'IP Address', accessor: 'ip_address' },
    { Header: 'Login Time', accessor: 'login_time' },
    { Header: 'Logout Time', accessor: 'logout_time' },
    { Header: 'Is Active', accessor: 'is_active' },
  ];

  return (
    <div className="container mt-5">
      <h1 className="text-center mb-4">Manage Users & Sessions</h1>

      <div className="mb-5">
        <h2>Users List</h2>
        <TableWithPagination
          endpoint="/users/"  // API endpoint to fetch users
          columns={userColumns}  // Columns to display in the table
          title="Users List"
          perPage={5}  // Limit to 5 items per page
        />
      </div>

      <div>
        <h2>User Sessions</h2>
        <TableWithPagination
          endpoint="/users/sessions/"  // API endpoint to fetch sessions
          columns={sessionColumns}  // Columns to display sessions
          title="User Sessions"
          perPage={5}  // Limit to 5 items per page
        />
      </div>
    </div>
  );
};

export default ManageUsersPage;
