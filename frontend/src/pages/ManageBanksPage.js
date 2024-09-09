import React, { useState, useEffect } from 'react';
import { Card, Typography, Button, Modal, TextField } from '@mui/material';
import { Container, Row, Col, Table, Spinner } from 'react-bootstrap';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import api from '../services/api'; // Axios instance

const ManageBanksPage = () => {
  const [banks, setBanks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedBank, setSelectedBank] = useState(null);
  const [modalMode, setModalMode] = useState('add');  // 'add' or 'edit'

  const [bankData, setBankData] = useState({
    name: '',
    code: '',
  });

  // Fetch all banks on component mount
  useEffect(() => {
    const fetchBanks = async () => {
      try {
        const response = await api.get('/banks');  // Fetch banks from API
        setBanks(response.data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching banks:', error);
        setLoading(false);
      }
    };

    fetchBanks();
  }, []);

  // Handle opening and closing modals
  const handleOpenModal = (mode, bank = null) => {
    setModalMode(mode);
    if (mode === 'edit' && bank) {
      setSelectedBank(bank);
      setBankData({ name: bank.name, code: bank.code });
    } else {
      setBankData({ name: '', code: '' });
    }
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setSelectedBank(null);
  };

  // Handle form submission for adding or editing a bank
  const handleSubmit = async () => {
    try {
      if (modalMode === 'add') {
        const response = await api.post('/banks', bankData);  // Add new bank
        setBanks([...banks, response.data]);
      } else if (modalMode === 'edit' && selectedBank) {
        const response = await api.put(`/banks/${selectedBank.id}`, bankData);  // Edit bank
        setBanks(banks.map((bank) => (bank.id === selectedBank.id ? response.data : bank)));
      }
      handleCloseModal();
    } catch (error) {
      console.error('Error saving bank:', error);
    }
  };

  // Handle deleting a bank
  const handleDelete = async (bankId) => {
    try {
      await api.delete(`/banks/${bankId}`);  // Delete bank
      setBanks(banks.filter((bank) => bank.id !== bankId));
    } catch (error) {
      console.error('Error deleting bank:', error);
    }
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
            startIcon={<AddIcon />}
            onClick={() => handleOpenModal('add')}
          >
            Add New Bank
          </Button>
        </Col>
      </Row>

      <Row className="mt-4">
        <Col md={12}>
          <Table striped bordered hover>
            <thead>
              <tr>
                <th>Name</th>
                <th>Code</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {banks.map((bank) => (
                <tr key={bank.id}>
                  <td>{bank.name}</td>
                  <td>{bank.code}</td>
                  <td>
                    <Button
                      variant="contained"
                      color="secondary"
                      startIcon={<EditIcon />}
                      onClick={() => handleOpenModal('edit', bank)}
                      className="me-2"
                    >
                      Edit
                    </Button>
                    <Button
                      variant="contained"
                      color="error"
                      startIcon={<DeleteIcon />}
                      onClick={() => handleDelete(bank.id)}
                    >
                      Delete
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Col>
      </Row>

      {/* Modal for Add/Edit Bank */}
      <Modal open={showModal} onClose={handleCloseModal}>
        <Card style={{ width: '30%', margin: '10% auto', padding: '20px' }}>
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
          <TextField
            fullWidth
            label="Bank Code"
            value={bankData.code}
            onChange={(e) => setBankData({ ...bankData, code: e.target.value })}
            margin="normal"
          />
          <Row className="mt-3">
            <Col md={6}>
              <Button variant="contained" color="primary" onClick={handleSubmit}>
                Save
              </Button>
            </Col>
            <Col md={6}>
              <Button variant="outlined" color="secondary" onClick={handleCloseModal}>
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
