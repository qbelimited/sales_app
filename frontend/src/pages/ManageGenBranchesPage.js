import React, { useEffect, useState } from 'react';
import { Card, Typography, Button, Modal, TextField } from '@mui/material';
import { Container, Row, Col, Table, Spinner, Pagination } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faEdit, faTrashAlt } from '@fortawesome/free-solid-svg-icons';
import api from '../services/api'; // Axios instance

const ManageGenBranchesPage = ({ showToast }) => {
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showBranchModal, setShowBranchModal] = useState(false);
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [selectedBranch, setSelectedBranch] = useState(null);
  const [modalMode, setModalMode] = useState('add'); // 'add' or 'edit'
  const [branchData, setBranchData] = useState({ name: '', ghpost_gps: '', address: '', city: '', region: '' });
  const [ghPostError, setGhPostError] = useState(''); // Error state for Ghana Post GPS

  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const branchesPerPage = 10;

  // Fetch current logged-in user and role
  const local_user = JSON.parse(localStorage.getItem('user'));
  const role_id = parseInt(local_user?.role_id) || local_user?.role?.id;

  // Fetch all branches on component mount and on pagination change
  useEffect(() => {
    const fetchBranches = async () => {
      setLoading(true);
      try {
        const response = await api.get(`/branches/?sort_by=created_at&per_page=${branchesPerPage}&page=${currentPage}`);
        setBranches(response.data.branches);
        setTotalPages(Math.ceil(response.data.total / branchesPerPage)); // Update total pages
      } catch (error) {
        console.error('Error fetching branches:', error);
        showToast('error', 'Failed to fetch branches. Please try again later.', 'Error');
      } finally {
        setLoading(false);
      }
    };
    fetchBranches();
  }, [showToast, currentPage]);

  // Handle pagination
  const paginate = (pageNumber) => setCurrentPage(pageNumber);

  // Handle opening and closing modals
  const handleOpenBranchModal = (mode, branch = null) => {
    setModalMode(mode);
    setGhPostError(''); // Reset error on modal open
    if (mode === 'edit' && branch) {
      setSelectedBranch(branch);
      setBranchData({ name: branch.name, ghpost_gps: branch.ghpost_gps, address: branch.address, city: branch.city, region: branch.region });
    } else {
      setBranchData({ name: '', ghpost_gps: '', address: '', city: '', region: '' });
    }
    setShowBranchModal(true);
  };

  const handleCloseBranchModal = () => {
    setShowBranchModal(false);
    setSelectedBranch(null);
  };

  // Handle form submission for adding or editing a branch
  const handleSubmitBranch = async () => {
    // Validate Ghana Post GPS to be exactly 11 characters
    if (branchData.ghpost_gps.length !== 11) {
      setGhPostError('Ghana Post GPS must be exactly 11 characters.');
      return; // Stop form submission if validation fails
    }

    try {
      if (modalMode === 'add') {
        const response = await api.post('/branches/', branchData); // Add new branch
        setBranches((prevBranches) => [...prevBranches, response.data]);
        showToast('success', 'Branch added successfully.', 'Success');
      } else if (modalMode === 'edit' && selectedBranch) {
        const response = await api.put(`/branches/${selectedBranch.id}`, branchData); // Edit branch
        setBranches((prevBranches) =>
          prevBranches.map((branch) => (branch.id === selectedBranch.id ? response.data : branch))
        );
        showToast('success', 'Branch updated successfully.', 'Success');
      }
      handleCloseBranchModal();
    } catch (error) {
      console.error('Error saving branch:', error);
      showToast('error', 'Failed to save branch. Please try again later.', 'Error');
    }
  };

  // Handle deleting a branch
  const handleDeleteBranch = async () => {
    if (!selectedBranch) {
      showToast('error', 'No branch selected for deletion.', 'Error');
      return;
    }

    try {
      await api.delete(`/branches/${selectedBranch.id}`); // Delete branch
      setBranches((prevBranches) => prevBranches.filter((branch) => branch.id !== selectedBranch.id));
      showToast('success', 'Branch deleted successfully.', 'Success');
      setShowDeleteConfirmation(false);
      setSelectedBranch(null);
    } catch (error) {
      console.error('Error deleting branch:', error);
      showToast('error', 'Failed to delete branch. Please try again later.', 'Error');
    }
  };

  // Handle opening delete confirmation modal
  const handleShowDeleteConfirmation = (branch) => {
    if (!branch) return;
    setSelectedBranch(branch);
    setShowDeleteConfirmation(true);
  };

  if (loading) return <Spinner animation="border" />;

  return (
    <Container className="mt-4">
      <Row>
        <Col md={12}>
          <Typography variant="h4" gutterBottom>
            Branch Management
          </Typography>
        </Col>
      </Row>
      <Row>
        <Col md={12}>
          {/* Add New Branch Button (visible for specific roles) */}
          {(role_id === 2 || role_id === 3) && (
            <Button
              variant="contained"
              color="primary"
              onClick={() => handleOpenBranchModal('add')}
            >
              <FontAwesomeIcon icon={faPlus} /> Add New Branch
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
                <th>Address</th>
                <th>Ghana Post GPS</th>
                <th>City</th>
                <th>Region</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {branches.map((branch) => (
                <tr key={branch.id}>
                  <td>{branch.name}</td>
                  <td>{branch.address}</td>
                  <td>{branch.ghpost_gps}</td>
                  <td>{branch.city}</td>
                  <td>{branch.region}</td>
                  <td>
                    {/* Edit and Delete buttons (visible for specific roles) */}
                    {(role_id === 2 || role_id === 3) && (
                      <>
                        <Button
                          variant="contained"
                          color="secondary"
                          onClick={() => handleOpenBranchModal('edit', branch)}
                          className="me-2"
                        >
                          <FontAwesomeIcon icon={faEdit} /> Edit
                        </Button>
                        <Button
                          variant="contained"
                          color="error"
                          onClick={() => handleShowDeleteConfirmation(branch)}
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

      {/* Modal for Add/Edit Branch */}
      <Modal
        open={showBranchModal}
        onClose={handleCloseBranchModal}
        style={{ overflow: 'auto' }}
      >
        <Card style={{ width: '50%', margin: '5% auto', padding: '20px', maxHeight: '80vh', overflowY: 'auto' }}>
          <Typography variant="h5" gutterBottom>
            {modalMode === 'add' ? 'Add New Branch' : 'Edit Branch'}
          </Typography>
          <TextField
            fullWidth
            label="Branch Name"
            value={branchData.name}
            onChange={(e) => setBranchData({ ...branchData, name: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Address"
            value={branchData.address}
            onChange={(e) => setBranchData({ ...branchData, address: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Ghana Post GPS"
            value={branchData.ghpost_gps}
            onChange={(e) => setBranchData({ ...branchData, ghpost_gps: e.target.value })}
            margin="normal"
            error={Boolean(ghPostError)} // Highlight field in red if there's an error
            helperText={ghPostError} // Display error message below the field
          />
          <TextField
            fullWidth
            label="City"
            value={branchData.city}
            onChange={(e) => setBranchData({ ...branchData, city: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Region"
            value={branchData.region}
            onChange={(e) => setBranchData({ ...branchData, region: e.target.value })}
            margin="normal"
          />
          <Row className="mt-3">
            <Col md={6}>
              <Button variant="contained" color="primary" onClick={handleSubmitBranch}>
                Save
              </Button>
            </Col>
            <Col md={6}>
              <Button variant="outlined" color="secondary" onClick={handleCloseBranchModal}>
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
            Are you sure you want to delete this branch?
          </Typography>
          <Row className="mt-3">
            <Col md={6}>
              <Button variant="contained" color="error" onClick={handleDeleteBranch}>
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

export default ManageGenBranchesPage;
