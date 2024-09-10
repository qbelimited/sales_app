import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Spinner, Alert, Row, Col } from 'react-bootstrap';
import api from '../services/api';  // Import the Axios instance

const ManageUsersPage = ({ showToast }) => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);  // Global loading state
  const [loadingSave, setLoadingSave] = useState(false);  // Loading state for saving updates
  const [loadingDelete, setLoadingDelete] = useState(null);  // Track loading state for specific delete action
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [error, setError] = useState(null);  // Error state to display error messages
  const [sortBy, setSortBy] = useState('created_at');  // Sort by field
  const [filterBy, setFilterBy] = useState('');  // Filter by name
  const [perPage, setPerPage] = useState(10);  // Items per page
  const [page, setPage] = useState(1);  // Page number
  const [totalPages, setTotalPages] = useState(1);  // Total number of pages
  const [totalUsers, setTotalUsers] = useState(0);  // Total number of users

  // Fetch users from the API on component mount
  useEffect(() => {
    const fetchUsers = async () => {
      setLoading(true);  // Set loading state
      try {
        const response = await api.get('/users/', {
          params: {
            sort_by: sortBy,
            per_page: perPage,
            page: page,
          },
        });

        // Extract users and pagination details
        setUsers(response.data.users || []);
        setTotalPages(response.data.pages || 1);
        setTotalUsers(response.data.total || 0);
      } catch (error) {
        console.error('Error fetching users:', error);
        setError('Error fetching users');
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, [sortBy, filterBy, perPage, page]);  // Re-fetch users when these states change

  // Handle opening the edit modal
  const handleEditClick = (user) => {
    setSelectedUser(user);
    setShowEditModal(true);
  };

  // Handle closing the modal
  const handleCloseModal = () => {
    setSelectedUser(null);
    setShowEditModal(false);
  };

  // Validate user form inputs
  const validateUser = () => {
    if (!selectedUser.name || !selectedUser.email || !selectedUser.role) {
      showToast('warning', 'Please ensure all fields are filled correctly.', 'Validation Error');
      return false;
    }
    return true;
  };

  // Handle saving the updated user information
  const handleSaveChanges = async () => {
    if (!validateUser()) return;

    setLoadingSave(true);
    try {
      await api.put(`/users/${selectedUser.id}`, selectedUser);  // Update the user via API
      setUsers(users.map((user) => (user.id === selectedUser.id ? selectedUser : user)));  // Update the state
      handleCloseModal();
      showToast('success', 'User updated successfully', 'Success');
    } catch (error) {
      console.error('Error updating user:', error);
      showToast('danger', 'Error updating user', 'Error');
    } finally {
      setLoadingSave(false);
    }
  };

  // Handle deleting a user
  const handleDeleteClick = async (userId) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      setLoadingDelete(userId);  // Set loading state for the specific user
      try {
        await api.delete(`/users/${userId}`);  // Delete the user via API
        setUsers(users.filter((user) => user.id !== userId));  // Remove the user from the state
        showToast('success', 'User deleted successfully', 'Success');
      } catch (error) {
        console.error('Error deleting user:', error);
        showToast('danger', 'Error deleting user', 'Error');
      } finally {
        setLoadingDelete(null);  // Reset loading state
      }
    }
  };

  if (loading) return <Spinner animation="border" />;  // Show spinner while loading

  return (
    <div className="container mt-4">
      <h2>Manage Users</h2>

      {/* Display an error message if any */}
      {error && <Alert variant="danger">{error}</Alert>}

      {/* Sorting, Filtering, Pagination Controls */}
      <Row className="mb-3">
        <Col md={4}>
          <Form.Control
            type="text"
            placeholder="Filter by Name"
            value={filterBy}
            onChange={(e) => setFilterBy(e.target.value)}
          />
        </Col>
        <Col md={4}>
          <Form.Control
            as="select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="created_at">Sort by Created Date</option>
            <option value="name">Sort by Name</option>
          </Form.Control>
        </Col>
        <Col md={4}>
          <Form.Control
            as="select"
            value={perPage}
            onChange={(e) => setPerPage(Number(e.target.value))}
          >
            <option value={5}>5 per page</option>
            <option value={10}>10 per page</option>
            <option value={20}>20 per page</option>
          </Form.Control>
        </Col>
      </Row>

      {/* Users Table */}
      <Table striped bordered hover>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.length > 0 ? users.map((user) => (
            <tr key={user.id}>
              <td>{user.name}</td>
              <td>{user.email}</td>
              <td>{user.role_id}</td>
              <td>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => handleEditClick(user)}
                  disabled={loadingSave || loadingDelete === user.id}
                >
                  Edit
                </Button>{' '}
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => handleDeleteClick(user.id)}
                  disabled={loadingDelete === user.id}
                >
                  {loadingDelete === user.id ? <Spinner animation="border" size="sm" /> : 'Delete'}
                </Button>
              </td>
            </tr>
          )) : (
            <tr>
              <td colSpan="4" className="text-center">No users found</td>
            </tr>
          )}
        </tbody>
      </Table>

      {/* Pagination Controls on the Table */}
      <Row className="justify-content-end">
        <Col md="auto">
          <Button
            variant="primary"
            onClick={() => setPage(page - 1)}
            disabled={page === 1}
          >
            Previous
          </Button>{' '}
          <Button
            variant="primary"
            onClick={() => setPage(page + 1)}
            disabled={page === totalPages}
          >
            Next
          </Button>
        </Col>
      </Row>

      {/* Edit User Modal */}
      {selectedUser && (
        <Modal show={showEditModal} onHide={handleCloseModal}>
          <Modal.Header closeButton>
            <Modal.Title>Edit User</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Form>
              <Form.Group className="mb-3">
                <Form.Label>Name</Form.Label>
                <Form.Control
                  type="text"
                  value={selectedUser.name}
                  onChange={(e) => setSelectedUser({ ...selectedUser, name: e.target.value })}
                />
              </Form.Group>
              <Form.Group className="mb-3">
                <Form.Label>Email</Form.Label>
                <Form.Control
                  type="email"
                  value={selectedUser.email}
                  onChange={(e) => setSelectedUser({ ...selectedUser, email: e.target.value })}
                />
              </Form.Group>
              <Form.Group className="mb-3">
                <Form.Label>Role</Form.Label>
                <Form.Control
                  as="select"
                  value={selectedUser.role_id}
                  onChange={(e) => setSelectedUser({ ...selectedUser, role_id: e.target.value })}
                >
                  <option value={1}>Admin</option>
                  <option value={2}>Manager</option>
                  <option value={3}>User</option>
                </Form.Control>
              </Form.Group>
            </Form>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={handleCloseModal}>
              Close
            </Button>
            <Button variant="primary" onClick={handleSaveChanges} disabled={loadingSave}>
              {loadingSave ? <Spinner animation="border" size="sm" /> : 'Save Changes'}
            </Button>
          </Modal.Footer>
        </Modal>
      )}
    </div>
  );
};

export default ManageUsersPage;
