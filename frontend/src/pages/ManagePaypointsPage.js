import React, { useEffect, useState } from 'react';
import { Card, Typography, Button, Modal, TextField } from '@mui/material';
import { Container, Row, Col, Table, Spinner, Pagination } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faEdit, faTrashAlt } from '@fortawesome/free-solid-svg-icons';
import api from '../services/api'; // Axios instance

const ManagePaypointsPage = ({ showToast }) => {
  const [paypoints, setPaypoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showPaypointModal, setShowPaypointModal] = useState(false);
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [selectedPaypoint, setSelectedPaypoint] = useState(null);
  const [modalMode, setModalMode] = useState('add'); // 'add' or 'edit'
  const [paypointData, setPaypointData] = useState({ name: '', location: '' });

  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const paypointsPerPage = 10;

  // Fetch current logged-in user and role
  const local_user = JSON.parse(localStorage.getItem('user'));
  const role_id = parseInt(local_user?.role_id) || local_user?.role?.id;

  // Fetch all paypoints on component mount and on pagination change
  useEffect(() => {
    const fetchPaypoints = async () => {
      setLoading(true);
      try {
        const response = await api.get(`/paypoints/?sort_by=created_at&per_page=${paypointsPerPage}&page=${currentPage}`);
        setPaypoints(response.data.paypoints);
        setTotalPages(Math.ceil(response.data.total / paypointsPerPage)); // Update total pages
      } catch (error) {
        console.error('Error fetching paypoints:', error);
        showToast('error', 'Failed to fetch paypoints. Please try again later.', 'Error');
      } finally {
        setLoading(false);
      }
    };
    fetchPaypoints();
  }, [showToast, currentPage]);

  // Handle pagination
  const paginate = (pageNumber) => setCurrentPage(pageNumber);

  // Handle opening and closing modals
  const handleOpenPaypointModal = (mode, paypoint = null) => {
    setModalMode(mode);
    if (mode === 'edit' && paypoint) {
      setSelectedPaypoint(paypoint);
      setPaypointData({ name: paypoint.name, location: paypoint.location });
    } else {
      setPaypointData({ name: '', location: '' });
    }
    setShowPaypointModal(true);
  };

  const handleClosePaypointModal = () => {
    setShowPaypointModal(false);
    setSelectedPaypoint(null);
  };

  // Handle form submission for adding or editing a paypoint
  const handleSubmitPaypoint = async () => {
    try {
      if (modalMode === 'add') {
        const response = await api.post('/paypoints/', paypointData); // Add new paypoint
        setPaypoints((prevPaypoints) => [...prevPaypoints, response.data]);
        showToast('success', 'Paypoint added successfully.', 'Success');
      } else if (modalMode === 'edit' && selectedPaypoint) {
        const response = await api.put(`/paypoints/${selectedPaypoint.id}`, paypointData); // Edit paypoint
        setPaypoints((prevPaypoints) =>
          prevPaypoints.map((paypoint) => (paypoint.id === selectedPaypoint.id ? response.data : paypoint))
        );
        showToast('success', 'Paypoint updated successfully.', 'Success');
      }
      handleClosePaypointModal();
    } catch (error) {
      console.error('Error saving paypoint:', error);
      showToast('error', 'Failed to save paypoint. Please try again later.', 'Error');
    }
  };

  // Handle deleting a paypoint
  const handleDeletePaypoint = async () => {
    if (!selectedPaypoint) {
      showToast('error', 'No paypoint selected for deletion.', 'Error');
      return;
    }

    try {
      await api.delete(`/paypoints/${selectedPaypoint.id}`); // Delete paypoint
      setPaypoints((prevPaypoints) => prevPaypoints.filter((paypoint) => paypoint.id !== selectedPaypoint.id));
      showToast('success', 'Paypoint deleted successfully.', 'Success');
      setShowDeleteConfirmation(false);
      setSelectedPaypoint(null);
    } catch (error) {
      console.error('Error deleting paypoint:', error);
      showToast('error', 'Failed to delete paypoint. Please try again later.', 'Error');
    }
  };

  // Handle opening delete confirmation modal
  const handleShowDeleteConfirmation = (paypoint) => {
    if (!paypoint) return;
    setSelectedPaypoint(paypoint);
    setShowDeleteConfirmation(true);
  };

  if (loading) return <Spinner animation="border" />;

  return (
    <Container className="mt-4">
      <Row>
        <Col md={12}>
          <Typography variant="h4" gutterBottom>
            Paypoint Management
          </Typography>
        </Col>
      </Row>
      <Row>
        <Col md={12}>
          {/* Add New Paypoint Button (visible for specific roles) */}
          {(role_id === 2 || role_id === 3) && (
            <Button
              variant="contained"
              color="primary"
              onClick={() => handleOpenPaypointModal('add')}
            >
              <FontAwesomeIcon icon={faPlus} /> Add New Paypoint
            </Button>
          )}
        </Col>
      </Row>

      <Row className="mt-4">
        <Col md={12}>
          <Table striped bordered hover>
            <thead>
              <tr>
                <th>Name</th>
                <th>Location</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {paypoints.map((paypoint) => (
                <tr key={paypoint.id}>
                  <td>{paypoint.name}</td>
                  <td>{paypoint.location}</td>
                  <td>
                    {/* Edit and Delete buttons (visible for specific roles) */}
                    {(role_id === 2 || role_id === 3) && (
                      <>
                        <Button
                          variant="contained"
                          color="secondary"
                          onClick={() => handleOpenPaypointModal('edit', paypoint)}
                          className="me-2"
                        >
                          <FontAwesomeIcon icon={faEdit} /> Edit
                        </Button>
                        <Button
                          variant="contained"
                          color="error"
                          onClick={() => handleShowDeleteConfirmation(paypoint)}
                        >
                          <FontAwesomeIcon icon={faTrashAlt} /> Delete
                        </Button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
          {/* Pagination */}
          <Pagination>
            {Array.from({ length: totalPages }, (_, index) => (
              <Pagination.Item key={index + 1} active={index + 1 === currentPage} onClick={() => paginate(index + 1)}>
                {index + 1}
              </Pagination.Item>
            ))}
          </Pagination>
        </Col>
      </Row>

      {/* Modal for Add/Edit Paypoint */}
      <Modal
        open={showPaypointModal}
        onClose={handleClosePaypointModal}
        style={{ overflow: 'auto' }}
      >
        <Card style={{ width: '50%', margin: '5% auto', padding: '20px', maxHeight: '80vh', overflowY: 'auto' }}>
          <Typography variant="h5" gutterBottom>
            {modalMode === 'add' ? 'Add New Paypoint' : 'Edit Paypoint'}
          </Typography>
          <TextField
            fullWidth
            label="Paypoint Name"
            value={paypointData.name}
            onChange={(e) => setPaypointData({ ...paypointData, name: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Location"
            value={paypointData.location}
            onChange={(e) => setPaypointData({ ...paypointData, location: e.target.value })}
            margin="normal"
          />
          <Row className="mt-3">
            <Col md={6}>
              <Button variant="contained" color="primary" onClick={handleSubmitPaypoint}>
                Save
              </Button>
            </Col>
            <Col md={6}>
              <Button variant="outlined" color="secondary" onClick={handleClosePaypointModal}>
                Cancel
              </Button>
            </Col>
          </Row>
        </Card>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        open={showDeleteConfirmation}
        onClose={() => setShowDeleteConfirmation(false)}
        style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}
      >
        <Card style={{ padding: '20px' }}>
          <Typography variant="h6" gutterBottom>
            Are you sure you want to delete this paypoint?
          </Typography>
          <Row className="mt-3">
            <Col md={6}>
              <Button variant="contained" color="error" onClick={handleDeletePaypoint}>
                Delete
              </Button>
            </Col>
            <Col md={6}>
              <Button variant="outlined" color="secondary" onClick={() => setShowDeleteConfirmation(false)}>
                Cancel
              </Button>
            </Col>
          </Row>
        </Card>
      </Modal>
    </Container>
  );
};

export default ManagePaypointsPage;
