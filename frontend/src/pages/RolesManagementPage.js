import React from 'react';
import TableWithPagination from '../components/TableWithPagination';

const ManageRolesPage = () => {
  const roleColumns = [
    { Header: 'Role Name', accessor: 'name' },
    { Header: 'Description', accessor: 'description' },
    { Header: 'Is Deleted', accessor: (row) => (row.is_deleted ? 'Yes' : 'No') },
    { Header: 'Created At', accessor: (row) => new Date(row.created_at).toLocaleDateString() },
  ];

  return (
    <div className="container mt-5">
      <h1 className="text-center mb-4">Manage Roles</h1>

      {/* TableWithPagination component for roles table */}
      <TableWithPagination
        endpoint="/roles/"  // API endpoint to fetch roles
        columns={roleColumns}  // Columns to display in the table
        title="Roles List"  // Title for the table
      />
    </div>
  );
};

export default ManageRolesPage;
