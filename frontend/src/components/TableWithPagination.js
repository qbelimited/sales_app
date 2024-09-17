import React, { useState, useEffect, useCallback } from 'react';
import { Table, Spinner, Row, Col, Button, Form, Modal, Badge } from 'react-bootstrap';
import { FaSort, FaSortUp, FaSortDown, FaPen, FaTrash, FaKey } from 'react-icons/fa';
import api from '../services/api';

const TableWithPagination = ({ endpoint, columns, title, showToast }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortBy, setSortBy] = useState('created_at');
  const [sortDirection, setSortDirection] = useState('asc');
  const [filterBy, setFilterBy] = useState('');
  const [perPage, setPerPage] = useState(10);
  const [page, setPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [showEditModal, setShowEditModal] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [branches, setBranches] = useState([]);
  const [selectedBranches, setSelectedBranches] = useState([]);
  const [roles, setRoles] = useState([]);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');

  // State for deletion modal
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [userToDelete, setUserToDelete] = useState(null);

  const fetchBranches = useCallback(async () => {
    try {
      const branchResponse = await api.get('/branches/?sort_by=created_at&per_page=1000&page=1');
      setBranches(branchResponse.data.branches || []);
    } catch (error) {
      console.error('Error fetching branches:', error);
    }
  }, []);

  const fetchRoles = useCallback(async () => {
    try {
      const roleResponse = await api.get('/roles/');
      setRoles(roleResponse.data || []);
    } catch (error) {
      console.error('Error fetching roles:', error);
    }
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(endpoint, {
        params: {
          sort_by: sortBy,
          sort_direction: sortDirection,
          filter_by: filterBy,
          per_page: perPage,
          page,
        },
      });

      setData(response.data.users || []);
      setTotalItems(response.data.total || 0);
      setTotalPages(response.data.pages || 1);
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Failed to fetch data. Please try again later.');
      showToast('danger', 'Failed to fetch data. Please try again later.', 'Error');
    } finally {
      setLoading(false);
    }
  }, [endpoint, sortBy, sortDirection, filterBy, perPage, page, showToast]);

  useEffect(() => {
    fetchData();
    fetchBranches();
    fetchRoles();
  }, [fetchData, fetchBranches, fetchRoles]);

  const handleSort = (column) => {
    if (sortBy === column) {
      setSortDirection((prevDirection) => (prevDirection === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(column);
      setSortDirection('asc');
    }
  };

  const getSortIcon = (column) => {
    if (sortBy === column) {
      return sortDirection === 'asc' ? <FaSortUp /> : <FaSortDown />;
    }
    return <FaSort />;
  };

  const handleFilterChange = (e) => {
    setFilterBy(e.target.value);
    setPage(1);
  };

  const handlePerPageChange = (e) => {
    setPerPage(Number(e.target.value));
    setPage(1);
  };

  const handleEditClick = (user) => {
    setCurrentUser({
      ...user,
      role_id: user.role ? user.role.id : '' // Set the role_id based on the user's current role
    });
    setSelectedBranches(user.branches ? user.branches.map(branch => branch.id) : []);
    setShowEditModal(true);
  };

  const handleDeleteClick = (userId) => {
    setUserToDelete(userId);
    setShowDeleteModal(true); // Show delete confirmation modal
  };

  const confirmDelete = async () => {
    try {
      await api.delete(`/users/${userToDelete}`);
      setData(data.filter((user) => user.id !== userToDelete));
      showToast('success', 'User deleted successfully', 'Success');
    } catch (error) {
      console.error('Error deleting user:', error);
      showToast('danger', 'Error deleting user', 'Error');
    } finally {
      setShowDeleteModal(false); // Hide delete confirmation modal
      setUserToDelete(null);
    }
  };

  const handleSaveChanges = async () => {
    try {
      await api.put(`/users/${currentUser.id}`, {
        ...currentUser,
        branches: selectedBranches,
        role_id: parseInt(currentUser.role_id, 10),
      });
      setData((prevData) =>
        prevData.map((user) => (user.id === currentUser.id ? currentUser : user))
      );
      setShowEditModal(false);
      showToast('success', 'User updated successfully.', 'Success');
    } catch (error) {
      console.error('Error updating user:', error);
      showToast('danger', 'Error updating user', 'Error');
    }
  };

  const handleBranchChange = (branchId) => {
    setSelectedBranches((prevSelected) =>
      prevSelected.includes(branchId)
        ? prevSelected.filter((id) => id !== branchId)
        : [...prevSelected, branchId]
    );
  };

  const handleUpdatePassword = async () => {
    try {
      await api.put(`/users/${currentUser.id}/password`, {
        current_password: currentPassword,
        new_password: newPassword,
      });
      showToast('success', 'Password updated successfully!', 'Success');
      setShowPasswordModal(false);
      setNewPassword('');
      setCurrentPassword(''); // Clear current password
    } catch (error) {
      console.error('Password update failed:', error);
      showToast('danger', 'Failed to update password! Please try again.', 'Error');
    }
  };

  const handleShowPasswordModal = (user) => {
    setCurrentUser(user);
    setShowPasswordModal(true);
  };

  if (loading) return <Spinner animation="border" />;

  return (
    <div>
      <Row className="mb-3">
        <Col>
          <h2>{title}</h2>
        </Col>
        <Col className="text-right">
          <h5>Total Users: {totalItems}</h5>
        </Col>
      </Row>

      {error && <p className="text-center text-danger">{error}</p>}

      <Row className="mb-3">
        <Col md={4}>
          <Form.Control
            type="text"
            placeholder="Filter by keyword"
            value={filterBy}
            onChange={handleFilterChange}
          />
        </Col>
        <Col md={4}>
          <Form.Control as="select" value={perPage} onChange={handlePerPageChange}>
            <option value={5}>5 per page</option>
            <option value={10}>10 per page</option>
            <option value={20}>20 per page</option>
          </Form.Control>
        </Col>
      </Row>

      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>#</th>
            {columns.map((col) => (
              <th
                key={col.accessor}
                onClick={() => handleSort(col.accessor)}
                style={{ cursor: 'pointer' }}
                aria-sort={sortBy === col.accessor ? sortDirection : 'none'}
              >
                {col.Header} {getSortIcon(col.accessor)}
              </th>
            ))}
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {data.length > 0 ? (
            data.map((item, index) => (
              <tr key={item.id}>
                <td>{(page - 1) * perPage + index + 1}</td>
                {columns.map((col) => (
                  <td key={col.Header}>
                    {typeof col.accessor === 'function'
                      ? col.accessor(item)
                      : item[col.accessor]}
                  </td>
                ))}
                <td>
                  <Button variant="link" size="sm" onClick={() => handleEditClick(item)}>
                    <FaPen />
                  </Button>
                  <Button variant="link" size="sm" onClick={() => handleShowPasswordModal(item)}>
                    <FaKey />
                  </Button>
                  <Button variant="link" size="sm" onClick={() => handleDeleteClick(item.id)}>
                    <FaTrash />
                  </Button>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={columns.length + 2} className="text-center">
                No records found
              </td>
            </tr>
          )}
        </tbody>
      </Table>

      <Row className="align-items-center">
        <Col md="auto">
          <p className="mb-0">
            Showing {(page - 1) * perPage + 1} to {Math.min(page * perPage, totalItems)} of{' '}
            {totalItems} users
          </p>
        </Col>
        <Col md="auto">
          <p className="mb-0">Page {page} of {totalPages}</p>
        </Col>
        <Col md="auto" className="ml-auto">
          <Button variant="primary" onClick={() => setPage(page - 1)} disabled={page === 1}>
            Previous
          </Button>{' '}
          <Button variant="primary" onClick={() => setPage(page + 1)} disabled={page === totalPages}>
            Next
          </Button>
        </Col>
      </Row>

      {/* Edit User Modal */}
      {currentUser && (
        <Modal show={showEditModal} onHide={() => setShowEditModal(false)}>
          <Modal.Header closeButton>
            <Modal.Title>Edit User</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Form>
              <Form.Group className="mb-3">
                <Form.Label>Name</Form.Label>
                <Form.Control
                  type="text"
                  value={currentUser.name}
                  onChange={(e) => setCurrentUser({ ...currentUser, name: e.target.value })}
                />
              </Form.Group>
              <Form.Group className="mb-3">
                <Form.Label>Email</Form.Label>
                <Form.Control
                  type="email"
                  value={currentUser.email}
                  onChange={(e) => setCurrentUser({ ...currentUser, email: e.target.value })}
                />
              </Form.Group>
              <Form.Group className="mb-3">
                <Form.Label>Role</Form.Label>
                <Form.Control
                  as="select"
                  value={currentUser.role_id || ''}
                  onChange={(e) => setCurrentUser({ ...currentUser, role_id: parseInt(e.target.value, 10) })}
                >
                  {roles.map((role) => (
                    <option key={role.id} value={role.id}>
                      {role.name}
                    </option>
                  ))}
                </Form.Control>
              </Form.Group>
              <Form.Group className="mb-3">
                <Form.Label>Branches</Form.Label>
                <Form.Control
                  as="select"
                  onChange={(e) => handleBranchChange(parseInt(e.target.value, 10))}
                  value=""
                >
                  <option value="" disabled>Select Branch to Add</option>
                  {branches
                    .filter(branch => !selectedBranches.includes(branch.id))
                    .map((branch) => (
                      <option key={branch.id} value={branch.id}>
                        {branch.name}
                      </option>
                    ))}
                </Form.Control>
                <div className="mt-2">
                  {selectedBranches.map(branchId => {
                    const branch = branches.find(b => b.id === branchId);
                    return (
                      <Badge key={branchId} pill variant="primary" className="mr-2">
                        {branch ? branch.name : branchId}
                        <Button
                          variant="link"
                          size="sm"
                          onClick={() => handleBranchChange(branchId)}
                          className="ml-1 text-white"
                        >
                          x
                        </Button>
                      </Badge>
                    );
                  })}
                </div>
              </Form.Group>
            </Form>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowEditModal(false)}>
              Close
            </Button>
            <Button variant="primary" onClick={handleSaveChanges}>
              Save Changes
            </Button>
          </Modal.Footer>
        </Modal>
      )}

      {/* Update Password Modal */}
      {currentUser && (
        <Modal show={showPasswordModal} onHide={() => setShowPasswordModal(false)}>
          <Modal.Header closeButton>
            <Modal.Title>Update Password</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Form>
              <Form.Group>
                <Form.Label>New Password</Form.Label>
                <Form.Control
                  type="password"
                  placeholder="Enter new password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
              </Form.Group>
            </Form>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowPasswordModal(false)}>
              Close
            </Button>
            <Button variant="primary" onClick={handleUpdatePassword}>
              Update Password
            </Button>
          </Modal.Footer>
        </Modal>
      )}

      {/* Delete Confirmation Modal */}
      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Deletion</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Are you sure you want to delete this user? This action cannot be undone.
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={confirmDelete}>
            Delete
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default TableWithPagination;
