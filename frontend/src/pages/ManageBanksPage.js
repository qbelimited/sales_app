import React, { useEffect, useState } from 'react';
import { Card, Typography, Button, Modal, TextField } from '@mui/material';
import { Container, Row, Col, Table, Spinner, Pagination } from 'react-bootstrap';
import api from '../services/api'; // Axios instance
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faEdit, faTrashAlt, faSitemap } from '@fortawesome/free-solid-svg-icons';

const ManageBanksPage = ({ showToast }) => {
  const [banks, setBanks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showBankModal, setShowBankModal] = useState(false);
  const [showBranchModal, setShowBranchModal] = useState(false);
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [showEditBranchModal, setShowEditBranchModal] = useState(false);
  const [showDeleteBranchConfirmation, setShowDeleteBranchConfirmation] = useState(false);
  const [selectedBank, setSelectedBank] = useState(null);
  const [selectedBranch, setSelectedBranch] = useState(null);
  const [modalMode, setModalMode] = useState('add'); // 'add' or 'edit'
  const [bankData, setBankData] = useState({ name: '' });
  const [branchData, setBranchData] = useState({ name: '', sort_code: '' });
  const [branches, setBranches] = useState([]);

  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const banksPerPage = 10;

  // Fetch all banks on component mount
  useEffect(() => {
    const fetchBanks = async () => {
      setLoading(true);
      try {
        const response = await api.get('/bank/'); // Fetch banks from API
        setBanks(response.data);
      } catch (error) {
        console.error('Error fetching banks:', error);
        showToast('error', 'Failed to fetch banks. Please try again later.', 'Error');
      } finally {
        setLoading(false);
      }
    };
    fetchBanks();
  }, [showToast]);

  // Handle pagination
  const indexOfLastBank = currentPage * banksPerPage;
  const indexOfFirstBank = indexOfLastBank - banksPerPage;
  const currentBanks = banks.slice(indexOfFirstBank, indexOfLastBank);

  const paginate = (pageNumber) => setCurrentPage(pageNumber);

  // Handle opening and closing modals
  const handleOpenBankModal = (mode, bank = null) => {
    setModalMode(mode);
    if (mode === 'edit' && bank) {
      setSelectedBank(bank);
      setBankData({ name: bank.name });
    } else {
      setBankData({ name: '' });
    }
    setShowBankModal(true);
  };

  const handleCloseBankModal = () => {
    setShowBankModal(false);
    setSelectedBank(null);
  };

  const handleOpenBranchModal = (bank) => {
    setSelectedBank(bank);
    setBranches(bank.bank_branches || []);
    setShowBranchModal(true);
  };

  const handleCloseBranchModal = () => {
    setShowBranchModal(false);
    setBranchData({ name: '', sort_code: '' });
  };

  // Handle form submission for adding or editing a bank
  const handleSubmitBank = async () => {
    try {
      if (modalMode === 'add') {
        const response = await api.post('/bank/', bankData); // Add new bank
        setBanks((prevBanks) => [...prevBanks, response.data]);
        showToast('success', 'Bank added successfully.', 'Success');
      } else if (modalMode === 'edit' && selectedBank) {
        const response = await api.put(`/bank/${selectedBank.id}`, bankData); // Edit bank
        setBanks((prevBanks) =>
          prevBanks.map((bank) => (bank.id === selectedBank.id ? response.data : bank))
        );
        showToast('success', 'Bank updated successfully.', 'Success');
      }
      handleCloseBankModal();
    } catch (error) {
      console.error('Error saving bank:', error);
      showToast('error', 'Failed to save bank. Please try again later.', 'Error');
    }
  };

  // Handle deleting a bank and its branches
  const handleDeleteBank = async () => {
    if (!selectedBank) {
      showToast('error', 'No bank selected for deletion.', 'Error');
      return;
    }

    try {
      await api.delete(`/bank/${selectedBank.id}`); // Delete bank
      setBanks((prevBanks) => prevBanks.filter((bank) => bank.id !== selectedBank.id));
      showToast('success', 'Bank deleted successfully.', 'Success');
      setShowDeleteConfirmation(false);
      setSelectedBank(null);
    } catch (error) {
      console.error('Error deleting bank:', error);
      showToast('error', 'Failed to delete bank. Please try again later.', 'Error');
    }
  };

  // Handle opening delete confirmation modal
  const handleShowDeleteConfirmation = (bank) => {
    if (!bank) return;
    setSelectedBank(bank);
    setShowDeleteConfirmation(true);
  };

  // Handle adding or editing branches
  const handleBranchSubmit = async () => {
    if (!selectedBank) {
      showToast('error', 'No bank selected for branch operation.', 'Error');
      return;
    }

    try {
      if (modalMode === 'add') {
        const response = await api.post(`/bank/bank-branches`, {
          bank_id: selectedBank.id, // Pass the selected bank's ID
          name: branchData.name,
          sort_code: branchData.sort_code,
          is_deleted: false
        });
        setBranches((prevBranches) => [...prevBranches, response.data]);
        showToast('success', 'Branch added successfully.', 'Success');
      } else if (modalMode === 'edit' && selectedBranch) {
        const response = await api.put(`/bank/bank-branches/${selectedBranch.id}`, branchData); // Edit branch
        setBranches((prevBranches) =>
          prevBranches.map((branch) =>
            branch.id === selectedBranch.id ? response.data : branch
          )
        );
        showToast('success', 'Branch updated successfully.', 'Success');
      }
      setShowEditBranchModal(false);
    } catch (error) {
      console.error('Error saving branch:', error);
      showToast('error', 'Failed to save branch. Please try again later.', 'Error');
    }
  };

  // Handle opening edit branch modal
  const handleEditBranch = (branch) => {
    if (!branch) return;
    setBranchData({ name: branch.name, sort_code: branch.sort_code, id: branch.id });
    setSelectedBranch(branch);
    setModalMode('edit');
    setShowEditBranchModal(true);
  };

  // Handle deleting a branch
  const handleDeleteBranch = async () => {
    if (!selectedBranch) {
      showToast('error', 'No branch selected for deletion.', 'Error');
      return;
    }

    try {
      await api.delete(`/bank/bank-branches/${selectedBranch.id}`); // Delete branch
      setBranches((prevBranches) => prevBranches.filter((branch) => branch.id !== selectedBranch.id));
      showToast('success', 'Branch deleted successfully.', 'Success');
      setShowDeleteBranchConfirmation(false);
      setSelectedBranch(null);
    } catch (error) {
      console.error('Error deleting branch:', error);
      showToast('error', 'Failed to delete branch. Please try again later.', 'Error');
    }
  };

  // Handle opening delete branch confirmation modal
  const handleShowDeleteBranchConfirmation = (branch) => {
    if (!branch) return;
    setSelectedBranch(branch);
    setShowDeleteBranchConfirmation(true);
  };

  if (loading) return <Spinner animation="border" />;

  return (
    <Container className="mt-4">
      <Row>
        <Col md={12}>
          <Typography variant="h4" gutterBottom>
            Bank and Branch Management
          </Typography>
        </Col>
      </Row>
      <Row>
        <Col md={12}>
          <Button
            variant="contained"
            color="primary"
            onClick={() => handleOpenBankModal('add')}
          >
            <FontAwesomeIcon icon={faPlus} /> Add New Bank
          </Button>
        </Col>
      </Row>

      <Row className="mt-4">
        <Col md={12}>
          <Table striped bordered hover>
            <thead>
              <tr>
                <th>Name</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {currentBanks.map((bank) => (
                <tr key={bank.id}>
                  <td>{bank.name}</td>
                  <td>
                    <Button
                      variant="contained"
                      color="secondary"
                      onClick={() => handleOpenBankModal('edit', bank)}
                      className="me-2"
                    >
                      <FontAwesomeIcon icon={faEdit} /> Edit
                    </Button>
                    <Button
                      variant="contained"
                      color="error"
                      onClick={() => handleShowDeleteConfirmation(bank)}
                    >
                      <FontAwesomeIcon icon={faTrashAlt} /> Delete
                    </Button>
                    <Button
                      variant="contained"
                      color="info"
                      onClick={() => handleOpenBranchModal(bank)}
                      className="ms-2"
                    >
                      <FontAwesomeIcon icon={faSitemap} /> Manage Branches
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
          {/* Pagination */}
          <Pagination>
            {Array.from({ length: Math.ceil(banks.length / banksPerPage) }, (_, index) => (
              <Pagination.Item key={index + 1} active={index + 1 === currentPage} onClick={() => paginate(index + 1)}>
                {index + 1}
              </Pagination.Item>
            ))}
          </Pagination>
        </Col>
      </Row>

      {/* Modal for Add/Edit Bank */}
      <Modal
        open={showBankModal}
        onClose={handleCloseBankModal}
        style={{ overflow: 'auto' }}
      >
        <Card style={{ width: '50%', margin: '5% auto', padding: '20px', maxHeight: '80vh', overflowY: 'auto' }}>
          <Typography variant="h5" gutterBottom>
            {modalMode === 'add' ? 'Add New Bank' : 'Edit Bank'}
          </Typography>
          <TextField
            fullWidth
            label="Bank Name"
            value={bankData.name}
            onChange={(e) => setBankData({ ...bankData, name: e.target.value })}
            margin="normal"
          />
          <Row className="mt-3">
            <Col md={6}>
              <Button variant="contained" color="primary" onClick={handleSubmitBank}>
                Save
              </Button>
            </Col>
            <Col md={6}>
              <Button variant="outlined" color="secondary" onClick={handleCloseBankModal}>
                Cancel
              </Button>
            </Col>
          </Row>
        </Card>
      </Modal>

      {/* Modal for Managing Branches */}
      <Modal
        open={showBranchModal}
        onClose={handleCloseBranchModal}
        style={{ overflow: 'auto' }}
      >
        <Card style={{ width: '70%', margin: '3% auto', padding: '20px', maxHeight: '80vh', overflowY: 'auto' }}>
          <Typography variant="h5" gutterBottom>
            Manage Branches for {selectedBank?.name}
          </Typography>
          <Table striped bordered hover>
            <thead>
              <tr>
                <th>Name</th>
                <th>Sort Code</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {branches.map((branch) => (
                <tr key={branch.id}>
                  <td>{branch.name}</td>
                  <td>{branch.sort_code}</td>
                  <td>
                    <Button
                      variant="contained"
                      color="secondary"
                      onClick={() => handleEditBranch(branch)}
                      className="me-2"
                    >
                      <FontAwesomeIcon icon={faEdit} /> Edit
                    </Button>
                    <Button
                      variant="contained"
                      color="error"
                      onClick={() => handleShowDeleteBranchConfirmation(branch)}
                    >
                      <FontAwesomeIcon icon={faTrashAlt} /> Delete
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
          <Button
            variant="contained"
            color="primary"
            onClick={() => {
              setBranchData({ name: '', sort_code: '' }); // Reset branch data for adding new branch
              setModalMode('add');
              setShowEditBranchModal(true);
            }}
            className="mt-3"
          >
            <FontAwesomeIcon icon={faPlus} /> Add New Branch
          </Button>
        </Card>
      </Modal>

      {/* Modal for Editing Branch */}
      <Modal
        open={showEditBranchModal}
        onClose={() => setShowEditBranchModal(false)}
        style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}
      >
        <Card style={{ width: '30%', padding: '20px' }}>
          <Typography variant="h5" gutterBottom>
            {modalMode === 'add' ? 'Add Branch' : 'Edit Branch'}
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
            label="Sort Code"
            value={branchData.sort_code}
            onChange={(e) => setBranchData({ ...branchData, sort_code: e.target.value })}
            margin="normal"
          />
          <Row className="mt-3">
            <Col md={6}>
              <Button variant="contained" color="primary" onClick={handleBranchSubmit}>
                Save
              </Button>
            </Col>
            <Col md={6}>
              <Button variant="outlined" color="secondary" onClick={() => setShowEditBranchModal(false)}>
                Cancel
              </Button>
            </Col>
          </Row>
        </Card>
      </Modal>

      {/* Delete Branch Confirmation Modal */}
      <Modal
        open={showDeleteBranchConfirmation}
        onClose={() => setShowDeleteBranchConfirmation(false)}
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
              <Button variant="outlined" color="secondary" onClick={() => setShowDeleteBranchConfirmation(false)}>
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
            Are you sure you want to delete this bank?
          </Typography>
          <Row className="mt-3">
            <Col md={6}>
              <Button variant="contained" color="error" onClick={handleDeleteBank}>
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

export default ManageBanksPage;
