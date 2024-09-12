import React, { useState, useEffect, useCallback } from 'react';
import { Table, Spinner, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import { FaSort, FaSortUp, FaSortDown } from 'react-icons/fa';
import api from '../services/api';
import { toast } from 'react-toastify';
import debounce from 'lodash.debounce';

const TableWithPagination = ({ endpoint, columns, title, perPage }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [roles, setRoles] = useState([]);
  const [sortBy, setSortBy] = useState('created_at');
  const [sortDirection, setSortDirection] = useState('asc');
  const [filterBy, setFilterBy] = useState('');
  const [page, setPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [showEditModal, setShowEditModal] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [newPassword, setNewPassword] = useState('');

  // Fetch data from the API
  const fetchData = useCallback(async () => {
    setLoading(true);
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
      setData(response.data.users || response.data.sessions || []);
      setTotalItems(response.data.total || 0);
      setTotalPages(response.data.pages || 1);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [endpoint, sortBy, sortDirection, filterBy, perPage, page]);

  // Fetch roles from the API
  const fetchRoles = useCallback(async () => {
    try {
      const response = await api.get('/roles/');
      setRoles(response.data);
    } catch (error) {
      console.error('Error fetching roles:', error);
      toast.error('Failed to load roles');
    }
  }, []);

  useEffect(() => {
    fetchData();
    if (endpoint === '/users/') fetchRoles(); // Fetch roles only for users
  }, [fetchData, fetchRoles, endpoint]);

  // Handle sorting
  const handleSort = (column) => {
    if (sortBy === column) {
      setSortDirection((prevDirection) => (prevDirection === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(column);
      setSortDirection('asc');
    }
  };

  // Get sort icon based on the sorting direction
  const getSortIcon = (column) => {
    if (sortBy === column) {
      return sortDirection === 'asc' ? <FaSortUp /> : <FaSortDown />;
    }
    return <FaSort />;
  };

  // Handle filter change with debounce to reduce API calls
  const handleFilterChange = debounce((e) => {
    setFilterBy(e.target.value);
    setPage(1); // Reset to the first page when filtering
  }, 300); // Adjust debounce timing as needed

  const handleEditClick = (user) => {
    setCurrentUser(user);
    setShowEditModal(true);
  };

  const handleDeleteClick = async (id) => {
    const isUser = endpoint.includes('users');
    const confirmMsg = isUser ? 'Are you sure you want to delete this user?' : 'Are you sure you want to end this session?';
    if (window.confirm(confirmMsg)) {
      try {
        await api.delete(`${endpoint}/${id}`);
        setData(data.filter((item) => item.id !== id)); // Remove the user/session from the list
        toast.success(isUser ? 'User deleted successfully' : 'Session ended successfully');
      } catch (error) {
        console.error(isUser ? 'Error deleting user:' : 'Error ending session:', error);
        toast.error(isUser ? 'Error deleting user' : 'Error ending session');
      }
    }
  };

  const handleSaveChanges = async () => {
    try {
      await api.put(`/users/${currentUser.id}`, currentUser); // Update the user
      setData(data.map((user) => (user.id === currentUser.id ? currentUser : user))); // Update state
      setShowEditModal(false);
      toast.success('User updated successfully');
    } catch (error) {
      console.error('Error updating user:', error);
      toast.error('Error updating user');
    }
  };

  const handlePasswordReset = async () => {
    if (!newPassword) {
      toast.error('Password cannot be empty');
      return;
    }

    try {
      await api.put(`/users/${currentUser.id}/password`, { password: newPassword });
      toast.success('Password reset successfully');
      setNewPassword('');
    } catch (error) {
      console.error('Error resetting password:', error);
      toast.error('Error resetting password');
    }
  };

  if (loading) return <Spinner animation="border" />;

  return (
    <div>
      <Row className="mb-3">
        <Col>
          <h2>{title}</h2>
        </Col>
        <Col className="text-right">
          <h5>Total Items: {totalItems}</h5>
        </Col>
      </Row>

      <Row className="mb-3">
        <Col md={4}>
          <Form.Control
            type="text"
            placeholder="Filter by keyword"
            onChange={handleFilterChange}
          />
        </Col>
      </Row>

      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>#</th>
            {columns.map((col) => (
              <th key={col.accessor} onClick={() => handleSort(col.accessor)} style={{ cursor: 'pointer' }}>
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
                  <td key={col.accessor}>{item[col.accessor]}</td>
                ))}
                <td>
                  <Button variant="primary" size="sm" onClick={() => handleEditClick(item)}>
                    Edit
                  </Button>{' '}
                  <Button variant="danger" size="sm" onClick={() => handleDeleteClick(item.id)}>
                    {endpoint.includes('users') ? 'Delete' : 'End'}
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
            Showing {(page - 1) * perPage + 1} to {Math.min(page * perPage, totalItems)} of {totalItems} items
          </p>
        </Col>
        <Col md="auto">
          <p className="mb-0">Page {page} of {totalPages}</p>
        </Col>
        <Col md="auto" className="ml-auto">
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
                  value={currentUser.role_id}
                  onChange={(e) => setCurrentUser({ ...currentUser, role_id: e.target.value })}
                >
                  {roles.map((role) => (
                    <option key={role.id} value={role.id}>
                      {role.name}
                    </option>
                  ))}
                </Form.Control>
              </Form.Group>
              <Form.Group className="mb-3">
                <Form.Label>Reset Password</Form.Label>
                <Form.Control
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter new password"
                />
                <Button variant="secondary" className="mt-2" onClick={handlePasswordReset}>
                  Reset Password
                </Button>
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
    </div>
  );
};

export default TableWithPagination;
