import React, { useState, useEffect } from 'react';
import { Table, Spinner, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import { FaSort, FaSortUp, FaSortDown } from 'react-icons/fa';
import api from '../services/api';
import { toast } from 'react-toastify';

const TableWithPagination = ({ endpoint, columns, title }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState('created_at');
  const [sortDirection, setSortDirection] = useState('asc');
  const [filterBy, setFilterBy] = useState('');
  const [perPage, setPerPage] = useState(10);
  const [page, setPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [showEditModal, setShowEditModal] = useState(false); // Modal for editing user
  const [currentUser, setCurrentUser] = useState(null); // Store the user being edited

  useEffect(() => {
    const fetchData = async () => {
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

        setData(response.data.users || []);
        setTotalItems(response.data.total || 0);
        setTotalPages(response.data.pages || 1);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [endpoint, sortBy, sortDirection, filterBy, perPage, page]);

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

  // Handle filter change
  const handleFilterChange = (e) => {
    setFilterBy(e.target.value);
    setPage(1);
  };

  // Handle per page change
  const handlePerPageChange = (e) => {
    setPerPage(Number(e.target.value));
    setPage(1);
  };

  // Handle edit click
  const handleEditClick = (user) => {
    setCurrentUser(user);
    setShowEditModal(true);
  };

  // Handle delete click
  const handleDeleteClick = async (userId) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await api.delete(`/users/${userId}`);
        setData(data.filter(user => user.id !== userId)); // Remove the user from the list
        toast.success('User deleted successfully');
      } catch (error) {
        console.error('Error deleting user:', error);
        toast.error('Error deleting user');
      }
    }
  };

  // Handle save changes for edit
  const handleSaveChanges = async () => {
    try {
      await api.put(`/users/${currentUser.id}`, currentUser);  // Update the user via API
      setData(data.map(user => (user.id === currentUser.id ? currentUser : user)));  // Update the state
      setShowEditModal(false);  // Close modal
    } catch (error) {
      console.error('Error updating user:', error);
      toast.error('Error updating user');
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
          <h5>Total Users: {totalItems}</h5>
        </Col>
      </Row>

      {/* Filtering and Pagination Controls */}
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
          <Form.Control
            as="select"
            value={perPage}
            onChange={handlePerPageChange}
          >
            <option value={5}>5 per page</option>
            <option value={10}>10 per page</option>
            <option value={20}>20 per page</option>
          </Form.Control>
        </Col>
      </Row>

      {/* Data Table */}
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
                  <Button variant="primary" size="sm" onClick={() => handleEditClick(item)}>Edit</Button>{' '}
                  <Button variant="danger" size="sm" onClick={() => handleDeleteClick(item.id)}>Delete</Button>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={columns.length + 2} className="text-center">No records found</td>
            </tr>
          )}
        </tbody>
      </Table>

      {/* Pagination Controls */}
      <Row className="align-items-center">
        <Col md="auto">
          <p className="mb-0">Showing {(page - 1) * perPage + 1} to {Math.min(page * perPage, totalItems)} of {totalItems} users</p>
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
                  value={currentUser.role.name}
                  onChange={(e) => setCurrentUser({ ...currentUser, role_name: e.target.value })}
                >
                  <option value={1}>Admin</option>
                  <option value={2}>Manager</option>
                  <option value={3}>User</option>
                </Form.Control>
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
