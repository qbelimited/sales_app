import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Spinner, Alert } from 'react-bootstrap';
import api from '../services/api';  // Import the Axios instance
import { isValidEmail } from '../utils/validators';  // Import the email validator

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

  // Fetch users from the API on component mount
  useEffect(() => {
    const fetchUsers = async () => {
      setLoading(true);  // Set loading state
      try {
        const response = await api.get('/users', {
          params: {
            sort_by: sortBy,
            filter_by: filterBy,
            per_page: perPage,
            page: page,
          },
        });
        setUsers(response.data);  // Set the users from the API response
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
    if (!selectedUser.name || !selectedUser.email || !isValidEmail(selectedUser.email) || !selectedUser.role) {
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
      <div className="mb-3">
        <Form.Control
          type="text"
          placeholder="Filter by Name"
          value={filterBy}
          onChange={(e) => setFilterBy(e.target.value)}
          className="mb-2"
        />
        <Form.Control
          as="select"
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="mb-2"
        >
          <option value="created_at">Sort by Created Date</option>
          <option value="name">Sort by Name</option>
        </Form.Control>
        <Form.Control
          as="select"
          value={perPage}
          onChange={(e) => setPerPage(Number(e.target.value))}
          className="mb-2"
        >
          <option value={5}>5 per page</option>
          <option value={10}>10 per page</option>
          <option value={20}>20 per page</option>
        </Form.Control>
        <Button variant="primary" onClick={() => setPage(page - 1)} disabled={page === 1}>Previous</Button>
        <Button variant="primary" onClick={() => setPage(page + 1)}>Next</Button>
      </div>

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
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.name}</td>
              <td>{user.email}</td>
              <td>{user.role}</td>
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
          ))}
        </tbody>
      </Table>

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
                  isInvalid={!isValidEmail(selectedUser.email)}  // Mark as invalid if email is not valid
                />
                <Form.Control.Feedback type="invalid">
                  Please provide a valid email address.
                </Form.Control.Feedback>
              </Form.Group>
              <Form.Group className="mb-3">
                <Form.Label>Role</Form.Label>
                <Form.Control
                  as="select"
                  value={selectedUser.role}
                  onChange={(e) => setSelectedUser({ ...selectedUser, role: e.target.value })}
                >
                  <option value="admin">Admin</option>
                  <option value="manager">Manager</option>
                  <option value="user">User</option>
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
