import React, { useState } from 'react';
import TableWithPagination from '../components/TableWithPagination';
import { Spinner, Alert } from 'react-bootstrap';

const ManageUsersPage = () => {
  // Pagination state for dynamic page sizes
  const [userPerPage, setUserPerPage] = useState(5);
  const [sessionPerPage, setSessionPerPage] = useState(5);

  // Columns for user list table
  const userColumns = [
    { Header: 'Name', accessor: 'name' },
    { Header: 'Email', accessor: 'email' },
    { Header: 'Role', accessor: 'role_name' }, // Display the role name
    { Header: 'Created At', accessor: 'created_at', sortType: 'datetime' }, // Added sort type for date
  ];

  // Columns for session list table
  const sessionColumns = [
    { Header: 'IP Address', accessor: 'ip_address' },
    { Header: 'Login Time', accessor: 'login_time', sortType: 'datetime' }, // Added sort type for date
    { Header: 'Logout Time', accessor: 'logout_time', sortType: 'datetime' },
    { Header: 'Is Active', accessor: 'is_active', Cell: ({ value }) => (value ? 'Yes' : 'No') },
  ];

  // Handle pagination change
  const handleUserPageSizeChange = (e) => setUserPerPage(Number(e.target.value));
  const handleSessionPageSizeChange = (e) => setSessionPerPage(Number(e.target.value));

  return (
    <div className="container mt-5">
      <h1 className="text-center mb-4">Manage Users & Sessions</h1>

      {/* Users List */}
      <div className="mb-5">
        <h2>Users List</h2>
        <label htmlFor="userPageSize" className="form-label">
          Items per page:
        </label>
        <select
          id="userPageSize"
          className="form-select mb-3"
          value={userPerPage}
          onChange={handleUserPageSizeChange}
        >
          <option value={5}>5</option>
          <option value={10}>10</option>
          <option value={20}>20</option>
        </select>

        <TableWithPagination
          endpoint="/users/" // API endpoint to fetch users
          columns={userColumns} // Columns for the user table
          title="Users List"
          perPage={userPerPage} // Dynamically controlled items per page
          errorComponent={<Alert variant="danger">Failed to load users data</Alert>}
          loadingComponent={<Spinner animation="border" />}
          noDataMessage="No users found."
        />
      </div>

      {/* User Sessions */}
      <div>
        <h2>User Sessions</h2>
        <label htmlFor="sessionPageSize" className="form-label">
          Items per page:
        </label>
        <select
          id="sessionPageSize"
          className="form-select mb-3"
          value={sessionPerPage}
          onChange={handleSessionPageSizeChange}
        >
          <option value={5}>5</option>
          <option value={10}>10</option>
          <option value={20}>20</option>
        </select>

        <TableWithPagination
          endpoint="/users/sessions/" // API endpoint to fetch sessions
          columns={sessionColumns} // Columns for the sessions table
          title="User Sessions"
          perPage={sessionPerPage} // Dynamically controlled items per page
          errorComponent={<Alert variant="danger">Failed to load sessions data</Alert>}
          loadingComponent={<Spinner animation="border" />}
          noDataMessage="No sessions found."
        />
      </div>
    </div>
  );
};

export default ManageUsersPage;
