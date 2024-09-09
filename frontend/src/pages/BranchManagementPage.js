import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Spinner, Form, Row, Col } from 'react-bootstrap';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';  // Axios instance

const BranchManagementPage = () => {
  const { bankId } = useParams();  // Get bank ID from the URL parameters
  const [branches, setBranches] = useState([]);
  const [bankName, setBankName] = useState('');
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedBranch, setSelectedBranch] = useState(null);
  const [branchData, setBranchData] = useState({ name: '', address: '' });
  const [modalMode, setModalMode] = useState('add');  // 'add' or 'edit'
  const navigate = useNavigate();

  // Fetch bank details and branches
  useEffect(() => {
    const fetchBranches = async () => {
      try {
        // Fetch bank details (optional)
        const bankResponse = await api.get(`/banks/${bankId}`);
        setBankName(bankResponse.data.name);

        // Fetch branches under the selected bank
        const branchesResponse = await api.get(`/banks/${bankId}/branches`);
        setBranches(branchesResponse.data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching branches:', error);
        setLoading(false);
      }
    };

    fetchBranches();
  }, [bankId]);

  // Open modal for add/edit
  const handleOpenModal = (mode, branch = null) => {
    setModalMode(mode);
    if (mode === 'edit' && branch) {
      setSelectedBranch(branch);
      setBranchData({ name: branch.name, address: branch.address });
    } else {
      setBranchData({ name: '', address: '' });
    }
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setSelectedBranch(null);
  };

  // Save or update branch
  const handleSubmit = async () => {
    try {
      if (modalMode === 'add') {
        const response = await api.post(`/banks/${bankId}/branches`, branchData);  // Add new branch
        setBranches([...branches, response.data]);
      } else if (modalMode === 'edit' && selectedBranch) {
        const response = await api.put(`/branches/${selectedBranch.id}`, branchData);  // Update branch
        setBranches(branches.map((branch) => (branch.id === selectedBranch.id ? response.data : branch)));
      }
      handleCloseModal();
    } catch (error) {
      console.error('Error saving branch:', error);
    }
  };

  // Delete a branch
  const handleDelete = async (branchId) => {
    try {
      await api.delete(`/branches/${branchId}`);  // Delete branch
      setBranches(branches.filter((branch) => branch.id !== branchId));
    } catch (error) {
      console.error('Error deleting branch:', error);
    }
  };

  if (loading) return <Spinner animation="border" />;

  return (
    <div className="container mt-4">
      <Row>
        <Col>
          <h2>Manage Branches for {bankName}</h2>
          <Button variant="primary" className="mb-3" onClick={() => handleOpenModal('add')}>
            Add Branch
          </Button>
          <Button variant="secondary" className="mb-3" onClick={() => navigate(-1)}>
            Back to Banks
          </Button>
        </Col>
      </Row>

      {/* Branches Table */}
      <Table striped bordered hover>
        <thead>
          <tr>
            <th>Name</th>
            <th>Address</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {branches.map((branch) => (
            <tr key={branch.id}>
              <td>{branch.name}</td>
              <td>{branch.address}</td>
              <td>
                <Button variant="secondary" className="me-2" onClick={() => handleOpenModal('edit', branch)}>
                  Edit
                </Button>
                <Button variant="danger" onClick={() => handleDelete(branch.id)}>
                  Delete
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      {/* Add/Edit Branch Modal */}
      <Modal show={showModal} onHide={handleCloseModal}>
        <Modal.Header closeButton>
          <Modal.Title>{modalMode === 'add' ? 'Add Branch' : 'Edit Branch'}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group controlId="branchName" className="mb-3">
              <Form.Label>Branch Name</Form.Label>
              <Form.Control
                type="text"
                value={branchData.name}
                onChange={(e) => setBranchData({ ...branchData, name: e.target.value })}
              />
            </Form.Group>
            <Form.Group controlId="branchAddress" className="mb-3">
              <Form.Label>Branch Address</Form.Label>
              <Form.Control
                type="text"
                value={branchData.address}
                onChange={(e) => setBranchData({ ...branchData, address: e.target.value })}
              />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseModal}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSubmit}>
            Save Changes
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default BranchManagementPage;
