import React, { useEffect, useState, useCallback } from 'react';
import { Card, Typography, Button, Modal, Chip, TextField } from '@mui/material';
import { Container, Row, Col, Table, Spinner, Pagination, Form } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faEdit, faTrash, faEye } from '@fortawesome/free-solid-svg-icons';
import api from '../services/api'; // Axios instance

const ManageSalesExecutivesPage = ({ showToast }) => {
  const [salesExecutives, setSalesExecutives] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showExecutiveModal, setShowExecutiveModal] = useState(false);
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [selectedExecutive, setSelectedExecutive] = useState(null);
  const [modalMode, setModalMode] = useState('add'); // 'add', 'edit' or 'view'
  const [executiveData, setExecutiveData] = useState({ name: '', code: '', phone_number: '', manager_id: '', branch_ids: [] });
  const [branches, setBranches] = useState([]);
  const [selectedBranches, setSelectedBranches] = useState([]);
  const [salesManagers, setSalesManagers] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const executivesPerPage = 10;
  const local_user = JSON.parse(localStorage.getItem('user')); // Fetch current logged-in user
  const role_id = parseInt(local_user?.role_id) || local_user?.role?.id;

  // Fetch sales executives, filtering based on manager_id
  useEffect(() => {
    const fetchSalesExecutives = async () => {
      setLoading(true);
      try {
        const response = await api.get(`/sales_executives/?sort_by=created_at&per_page=${executivesPerPage}&page=${currentPage}`);
        const allExecutives = response.data.sales_executives;
        const filteredExecutives = local_user.manager_id
          ? allExecutives.filter(executive => executive.manager_id === local_user.manager_id)
          : allExecutives;

        setSalesExecutives(filteredExecutives);
        setTotalPages(Math.ceil(response.data.total / executivesPerPage));
      } catch (error) {
        console.error('Error fetching sales executives:', error);
        showToast('error', 'Failed to fetch sales executives. Please try again later.', 'Error');
      } finally {
        setLoading(false);
      }
    };
    fetchSalesExecutives();
  }, [showToast, currentPage, local_user.manager_id]);

  // Fetch branches and sales managers
  const fetchBranches = useCallback(async () => {
    try {
      const branchResponse = await api.get('/branches/?sort_by=created_at&per_page=1000&page=1');
      setBranches(branchResponse.data.branches || []);
    } catch (error) {
      console.error('Error fetching branches:', error);
    }
  }, []);

  const fetchSalesManagers = useCallback(async () => {
    try {
      const response = await api.get('/dropdown/', {
        params: { type: 'users_with_roles', role_id: 4 }, // Fetch users with role_id 4 (sales managers)
      });
      setSalesManagers(response.data);
    } catch (error) {
      console.error('Failed to fetch sales managers');
    }
  }, []);

  useEffect(() => {
    fetchBranches();
    fetchSalesManagers();
  }, [fetchBranches, fetchSalesManagers]);

  // Handle pagination
  const paginate = (pageNumber) => setCurrentPage(pageNumber);

  // Handle opening and closing modals
  const handleOpenExecutiveModal = (mode, executive = null) => {
    setModalMode(mode);
    if (mode === 'edit' && executive) {
      setSelectedExecutive(executive);
      setExecutiveData({
        name: executive.name,
        code: executive.code,
        phone_number: executive.phone_number,
        manager_id: executive.manager_id,
        branch_ids: executive.branch_ids || [],
      });
      setSelectedBranches(executive.branch_ids || []); // Preselect branches
    } else if (mode === 'view' && executive) {
      setSelectedExecutive(executive);
      setExecutiveData({
        name: executive.name,
        code: executive.code,
        phone_number: executive.phone_number,
        manager_id: executive.manager_id,
        branch_ids: executive.branch_ids || [],
      });
      setSelectedBranches(executive.branch_ids || []); // Preselect branches for viewing
    } else {
      setExecutiveData({ name: '', code: '', phone_number: '', manager_id: '', branch_ids: [] });
      setSelectedBranches([]);
    }
    setShowExecutiveModal(true);
  };

  const handleCloseExecutiveModal = () => {
    setShowExecutiveModal(false);
    setSelectedExecutive(null);
  };

  // Handle form submission for adding or editing an executive
  const handleSubmitExecutive = async () => {
    try {
      if (modalMode === 'add') {
        const response = await api.post('/sales_executives/', { ...executiveData, branch_ids: selectedBranches }); // Add new executive
        setSalesExecutives((prevExecutives) => [...prevExecutives, response.data]);
        showToast('success', 'Sales executive added successfully.', 'Success');
      } else if (modalMode === 'edit' && selectedExecutive) {
        const response = await api.put(`/sales_executives/${selectedExecutive.id}`, { ...executiveData, branch_ids: selectedBranches }); // Edit executive
        setSalesExecutives((prevExecutives) =>
          prevExecutives.map((executive) => (executive.id === selectedExecutive.id ? response.data : executive))
        );
        showToast('success', 'Sales executive updated successfully.', 'Success');
      }
      handleCloseExecutiveModal();
    } catch (error) {
      console.error('Error saving sales executive:', error);
      showToast('error', 'Failed to save sales executive. Please try again later.', 'Error');
    }
  };

  // Handle deleting an executive with confirmation modal
  const handleDeleteExecutive = async () => {
    if (!selectedExecutive) {
      showToast('error', 'No sales executive selected for deletion.', 'Error');
      return;
    }

    try {
      await api.delete(`/sales_executives/${selectedExecutive.id}`); // Delete executive
      setSalesExecutives((prevExecutives) => prevExecutives.filter((executive) => executive.id !== selectedExecutive.id));
      showToast('success', 'Sales executive deleted successfully.', 'Success');
      setShowDeleteConfirmation(false);
      setSelectedExecutive(null);
    } catch (error) {
      console.error('Error deleting sales executive:', error);
      showToast('error', 'Failed to delete sales executive. Please try again later.', 'Error');
    }
  };

  // Handle branch selection/deselection
  const handleBranchChange = (branchId) => {
    setSelectedBranches((prevSelected) =>
      prevSelected.includes(branchId)
        ? prevSelected.filter((id) => id !== branchId)
        : [...prevSelected, branchId]
    );
  };

  // Render action buttons based on role
  const renderActions = (executive) => (
    <>
      <Button
        variant="primary"
        size="sm"
        className="me-2"
        onClick={() => handleOpenExecutiveModal('view', executive)}
      >
        <FontAwesomeIcon icon={faEye} />
      </Button>
      {role_id === 3 || role_id === 2 ? (
        <>
          <Button
            variant="warning"
            size="sm"
            className="me-2"
            onClick={() => handleOpenExecutiveModal('edit', executive)}
          >
            <FontAwesomeIcon icon={faEdit} />
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={() => {
              setSelectedExecutive(executive);
              setShowDeleteConfirmation(true);
            }}
          >
            <FontAwesomeIcon icon={faTrash} />
          </Button>
        </>
      ) : null}
    </>
  );

  if (loading) return <Spinner animation="border" />;

  return (
    <Container className="mt-4">
      <Row>
        <Col md={12}>
          <Typography variant="h4" gutterBottom>
            Sales Executive Management
          </Typography>
        </Col>
      </Row>
      {role_id === 2 || role_id === 3 ? (
        <Row>
          <Col md={12}>
            <Button
              variant="contained"
              color="primary"
              onClick={() => handleOpenExecutiveModal('add')}
            >
              <FontAwesomeIcon icon={faPlus} /> Add New Sales Executive
              </Button>
          </Col>
        </Row>
      ) : null}

      <Row className="mt-4">
        <Col md={12}>
          <Table striped bordered hover>
            <thead>
              <tr>
                <th>Name</th>
                <th>Code</th>
                <th>Phone Number</th>
                <th>Manager</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {salesExecutives.map((executive) => {
                const manager = salesManagers.find((sm) => sm.id === executive.manager_id);
                return (
                  <tr key={executive.id}>
                    <td>{executive.name}</td>
                    <td>{executive.code}</td>
                    <td>{executive.phone_number}</td>
                    <td>{manager ? manager.name : 'Unassigned'}</td>
                    <td>{renderActions(executive)}</td>
                  </tr>
                );
              })}
            </tbody>
          </Table>

          {/* Pagination */}
          <Pagination className="justify-content-center">
            {Array.from({ length: totalPages }, (_, index) => (
              <Pagination.Item key={index + 1} active={index + 1 === currentPage} onClick={() => paginate(index + 1)}>
                {index + 1}
              </Pagination.Item>
            ))}
          </Pagination>
        </Col>
      </Row>

      {/* Modal for Add/Edit/View Sales Executive */}
      <Modal
        open={showExecutiveModal}
        onClose={handleCloseExecutiveModal}
        style={{ overflow: 'auto' }}
      >
        <Card style={{ width: '50%', margin: '5% auto', padding: '20px', maxHeight: '80vh', overflowY: 'auto' }}>
          <Typography variant="h5" gutterBottom>
            {modalMode === 'add' ? 'Add New Sales Executive' : modalMode === 'edit' ? 'Edit Sales Executive' : 'View Sales Executive'}
          </Typography>

          <TextField
            fullWidth
            label="Executive Name"
            value={executiveData.name}
            onChange={(e) => setExecutiveData({ ...executiveData, name: e.target.value })}
            margin="normal"
            disabled={modalMode === 'view'} // Disable fields if in view mode
          />
          <TextField
            fullWidth
            label="Code"
            value={executiveData.code}
            onChange={(e) => setExecutiveData({ ...executiveData, code: e.target.value })}
            margin="normal"
            disabled={modalMode === 'view'} // Disable fields if in view mode
          />
          <TextField
            fullWidth
            label="Phone Number"
            value={executiveData.phone_number}
            onChange={(e) => setExecutiveData({ ...executiveData, phone_number: e.target.value })}
            margin="normal"
            disabled={modalMode === 'view'} // Disable fields if in view mode
          />

          <Form.Group className="mb-3">
            <Form.Label>Sale Manager</Form.Label>
            <Form.Control
              as="select"
              value={executiveData.manager_id}
              onChange={(e) => setExecutiveData({ ...executiveData, manager_id: parseInt(e.target.value, 10) })}
              disabled={modalMode === 'view'}
            >
              <option value="" disabled>Select Sales Manager</option>
              {salesManagers.map((manager) => (
                <option key={manager.id} value={manager.id}>
                  {manager.name}
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
              disabled={modalMode === 'view'}
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
                  <Chip
                    key={branchId}
                    label={branch ? branch.name : branchId}
                    onDelete={modalMode !== 'view' ? () => handleBranchChange(branchId) : undefined}
                    color="primary"
                    className="mr-2"
                  />
                );
              })}
            </div>
          </Form.Group>

          {/* Buttons */}
          {modalMode !== 'view' && (
            <Row className="mt-3">
              <Col md={6}>
                <Button variant="contained" color="primary" onClick={handleSubmitExecutive}>
                  Save
                </Button>
              </Col>
              <Col md={6}>
                <Button variant="outlined" color="secondary" onClick={handleCloseExecutiveModal}>
                  Cancel
                </Button>
              </Col>
            </Row>
          )}
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
            Are you sure you want to delete this sales executive?
          </Typography>
          <Row className="mt-3">
            <Col md={6}>
              <Button variant="contained" color="error" onClick={handleDeleteExecutive}>
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

export default ManageSalesExecutivesPage;

