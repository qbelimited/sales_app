import React, { useState, useEffect, useCallback } from 'react';
import { Modal, Button, Table, Spinner, Form, Alert } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEdit, faTrashAlt, faPlus, faFileDownload, faFileUpload } from '@fortawesome/free-solid-svg-icons';
import api from '../services/api';
import { saveAs } from 'file-saver';

const InceptionsPage = ({ showToast }) => {
  const [inceptions, setInceptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentInception, setCurrentInception] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [sales, setSales] = useState([]);
  const [loadingSubmit, setLoadingSubmit] = useState(false);
  const [file, setFile] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);

  // Fetch sales for the dropdown
  const fetchSales = useCallback(async () => {
    try {
      const response = await api.get('/sales/');
      setSales(response.data.sales);
    } catch (err) {
      console.error('Error fetching sales:', err);
      showToast('danger', 'Failed to load sales.', 'Error');
    }
  }, [showToast]);

  const fetchInceptions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/inceptions/');
      setInceptions(response.data);
    } catch (err) {
      console.error('Error fetching inceptions:', err);
      setError('Failed to load inceptions.');
      showToast('danger', 'Failed to load inceptions.', 'Error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchInceptions();
    fetchSales();
  }, [fetchInceptions, fetchSales]);

  const handleShowAddModal = () => {
    setCurrentInception(null);
    setShowAddModal(true);
  };

  const handleCloseAddModal = () => {
    setShowAddModal(false);
  };

  const handleShowEditModal = (inception) => {
    setCurrentInception(inception);
    setShowEditModal(true);
  };

  const handleCloseEditModal = () => {
    setCurrentInception(null);
    setShowEditModal(false);
  };

  const handleShowDeleteModal = (inception) => {
    setCurrentInception(inception);
    setShowDeleteModal(true);
  };

  const handleCloseDeleteModal = () => {
    setCurrentInception(null);
    setShowDeleteModal(false);
  };

  const handleShowUploadModal = () => {
    setShowUploadModal(true);
  };

  const handleCloseUploadModal = () => {
    setFile(null);
    setShowUploadModal(false);
  };

  const validateData = (data) => {
    if (data.amount_received <= 0) {
      showToast('danger', 'Amount Received must be a positive number.', 'Error');
      return false;
    }
    return true;
  };

  const isDuplicateSaleId = (saleId) => {
    return inceptions.some(inception => inception.sale_id === saleId);
  };

  const addInception = async (data) => {
    if (!validateData(data) || isDuplicateSaleId(data.sale_id)) {
      if (isDuplicateSaleId(data.sale_id)) {
        showToast('danger', 'Sale ID already exists.', 'Error');
      }
      return;
    }
    setLoadingSubmit(true);
    try {
      await api.post('/inceptions/', data);
      showToast('success', 'Inception created successfully.', 'Success');
      fetchInceptions();
      handleCloseAddModal();
    } catch (err) {
      console.error('Error adding inception:', err);
      showToast('danger', 'Failed to save inception.', 'Error');
    } finally {
      setLoadingSubmit(false);
    }
  };

  const editInception = async (data) => {
    if (!validateData(data)) return;
    setLoadingSubmit(true);
    try {
      await api.put(`/inceptions/${currentInception.id}`, data);
      showToast('success', 'Inception updated successfully.', 'Success');
      fetchInceptions();
      handleCloseEditModal();
    } catch (err) {
      console.error('Error updating inception:', err);
      showToast('danger', 'Failed to update inception.', 'Error');
    } finally {
      setLoadingSubmit(false);
    }
  };

  const deleteInception = async () => {
    setLoadingSubmit(true);
    try {
      await api.delete(`/inceptions/${currentInception.id}`);
      showToast('success', 'Inception deleted successfully.', 'Success');
      fetchInceptions();
      handleCloseDeleteModal();
    } catch (err) {
      console.error('Error deleting inception:', err);
      showToast('danger', 'Failed to delete inception.', 'Error');
    } finally {
      setLoadingSubmit(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
      sale_id: parseInt(formData.get('sale_id'), 10),
      amount_received: parseFloat(formData.get('amount_received')),
      received_at: new Date(formData.get('received_at')).toISOString(),
      description: formData.get('description'),
    };

    if (currentInception) {
      editInception(data);
    } else {
      addInception(data);
    }
  };

  const downloadTemplate = () => {
    const templateData = [
      ['Sale ID', 'Amount Received', 'Received At', 'Description'],
      ['', '', 'dd/mm/yyyy', '']
    ];
    const csvContent = templateData.map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    saveAs(blob, 'inception_template.csv');
  };

  const uploadCSV = async () => {
    if (!file) {
      console.error('No file selected for upload');
      showToast('danger', 'No file selected for upload.', 'Error');
      return;
    }

    setUploadLoading(true);
    const reader = new FileReader();
    reader.onload = async (event) => {
      const csvData = event.target.result;
      const rows = csvData.split('\n').slice(1); // Skip header row

      const inceptionsToAdd = [];
      for (const row of rows) {
        const trimmedRow = row.trim();
        if (!trimmedRow) continue;

        const columns = trimmedRow.split(',');
        if (columns.length < 4) {
          console.error(`Row does not contain enough columns: ${trimmedRow}`);
          showToast('danger', 'Row does not contain enough columns.', 'Error');
          continue;
        }

        const [sale_id, amount_received, received_at, description] = columns;

        // Date parsing logic
        const dateParts = received_at.split('/');
        if (dateParts.length !== 3) {
          console.error(`Received At date is not valid: ${received_at}`);
          showToast('danger', 'Received At date is not valid.', 'Error');
          continue;
        }

        // Construct the date in the format YYYY-MM-DD
        const day = dateParts[0].padStart(2, '0'); // Pad day with leading zero if needed
        const month = dateParts[1].padStart(2, '0'); // Pad month with leading zero if needed
        const year = dateParts[2];
        const formattedDateString = `${year}-${month}-${day}T00:00:00`; // Use T00:00:00 for a full date-time string
        const formattedDate = new Date(formattedDateString);
        if (isNaN(formattedDate.getTime())) {
          console.error(`Invalid date format: ${received_at}`);
          showToast('danger', 'Invalid date format in Received At.', 'Error');
          continue;
        }

        const saleId = parseInt(sale_id, 10);
        // Check for duplicates
        if (isDuplicateSaleId(saleId)) {
          console.error(`Duplicate Sale ID: ${saleId}`);
          showToast('danger', `Duplicate Sale ID: ${saleId}`, 'Error');
          continue;
        }

        inceptionsToAdd.push({
          sale_id: saleId,
          amount_received: parseFloat(amount_received),
          received_at: formattedDate.toISOString(),
          description: description.trim(),
        });
      }

      for (const inception of inceptionsToAdd) {
        await addInception(inception);
      }
      showToast('success', 'Inceptions uploaded successfully.', 'Success');
      handleCloseUploadModal();
    };

    reader.onerror = (error) => {
      console.error('Error reading file:', error);
      showToast('danger', 'Failed to read the CSV file.', 'Error');
    };

    reader.readAsText(file);
  };

  return (
    <div className="container mt-5">
      <h1 className="text-center mb-4">Manage Inceptions</h1>
      <Alert variant="info" className="text-center">
        Please download the template file, fill it out, and upload it to add inceptions.
      </Alert>
      {loading && <Spinner animation="border" variant="primary" />}
      {error && <Alert variant="danger">{error}</Alert>}

      <Button variant="primary" onClick={handleShowAddModal} className="mb-3">
        <FontAwesomeIcon icon={faPlus} aria-hidden="true" /> Add Inception
      </Button>
      <Button variant="info" onClick={downloadTemplate} className="mb-3 mx-2" aria-label="Download Template">
        <FontAwesomeIcon icon={faFileDownload} aria-hidden="true" /> Download Template
      </Button>
      <Button variant="secondary" onClick={handleShowUploadModal} className="mb-3 mx-2" aria-label="Upload CSV">
        <FontAwesomeIcon icon={faFileUpload} aria-hidden="true" /> Upload CSV
      </Button>

      <Table striped bordered hover responsive className="mt-3">
        <thead>
          <tr>
            <th>ID</th>
            <th>Sale ID</th>
            <th>Amount Received</th>
            <th>Received At</th>
            <th>Description</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {inceptions.map(inception => (
            <tr key={inception.id}>
              <td>{inception.id}</td>
              <td>{inception.sale_id}</td>
              <td>{inception.amount_received.toFixed(2)}</td>
              <td>{new Date(inception.received_at).toLocaleString()}</td>
              <td>{inception.description}</td>
              <td>
                <Button variant="warning" onClick={() => handleShowEditModal(inception)} aria-label={`Edit inception ${inception.id}`}>
                  <FontAwesomeIcon icon={faEdit} aria-hidden="true" /> Edit
                </Button>
                <Button variant="danger" onClick={() => handleShowDeleteModal(inception)} aria-label={`Delete inception ${inception.id}`}>
                  <FontAwesomeIcon icon={faTrashAlt} aria-hidden="true" /> Delete
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      {/* Add Inception Modal */}
      <Modal show={showAddModal} onHide={handleCloseAddModal}>
        <Modal.Header closeButton>
          <Modal.Title>Add Inception</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form onSubmit={handleSubmit}>
            <Form.Group controlId="formSaleId">
              <Form.Label>Sale ID</Form.Label>
              <Form.Control as="select" name="sale_id" required>
                <option value="">Select Sale</option>
                {sales.map(sale => (
                  <option key={sale.id} value={sale.id}>
                    {sale.id} - {sale.serial_number} - {sale.policy_type?.name || 'N/A'} - {sale.amount}
                  </option>
                ))}
              </Form.Control>
            </Form.Group>
            <Form.Group controlId="formAmountReceived">
              <Form.Label>Amount Received</Form.Label>
              <Form.Control type="number" name="amount_received" required min="0" step="0.01" />
            </Form.Group>
            <Form.Group controlId="formReceivedAt">
              <Form.Label>Received At</Form.Label>
              <Form.Control type="datetime-local" name="received_at" required />
            </Form.Group>
            <Form.Group controlId="formDescription">
              <Form.Label>Description</Form.Label>
              <Form.Control type="text" name="description" required />
            </Form.Group>
            <Button variant="primary" type="submit" disabled={loadingSubmit}>
              {loadingSubmit ? <Spinner as="span" animation="border" size="sm" /> : 'Create'}
            </Button>
          </Form>
        </Modal.Body>
      </Modal>

      {/* Edit Inception Modal */}
      <Modal show={showEditModal} onHide={handleCloseEditModal}>
        <Modal.Header closeButton>
          <Modal.Title>Edit Inception</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {currentInception && (
            <Form onSubmit={handleSubmit}>
              <Form.Group controlId="formSaleId">
                <Form.Label>Sale ID</Form.Label>
                <Form.Control as="select" name="sale_id" defaultValue={currentInception.sale_id} required>
                  {sales.map(sale => (
                    <option key={sale.id} value={sale.id}>
                      {sale.id} - {sale.serial_number} - {sale.policy_type?.name || 'N/A'} - {sale.amount}
                    </option>
                  ))}
                </Form.Control>
              </Form.Group>
              <Form.Group controlId="formAmountReceived">
                <Form.Label>Amount Received</Form.Label>
                <Form.Control type="number" name="amount_received" defaultValue={currentInception.amount_received} required min="0" step="0.01" />
              </Form.Group>
              <Form.Group controlId="formReceivedAt">
                <Form.Label>Received At</Form.Label>
                <Form.Control type="datetime-local" name="received_at" defaultValue={new Date(currentInception.received_at).toISOString().slice(0, 16)} required />
              </Form.Group>
              <Form.Group controlId="formDescription">
                <Form.Label>Description</Form.Label>
                <Form.Control type="text" name="description" defaultValue={currentInception.description} required />
              </Form.Group>
              <Button variant="primary" type="submit" disabled={loadingSubmit}>
                {loadingSubmit ? <Spinner as="span" animation="border" size="sm" /> : 'Update'}
              </Button>
            </Form>
          )}
        </Modal.Body>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal show={showDeleteModal} onHide={handleCloseDeleteModal}>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Deletion</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>Are you sure you want to delete this inception? This action cannot be undone.</p>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseDeleteModal}>Cancel</Button>
          <Button variant="danger" onClick={deleteInception} disabled={loadingSubmit}>
            {loadingSubmit ? <Spinner as="span" animation="border" size="sm" /> : 'Delete'}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Upload CSV Modal */}
      <Modal show={showUploadModal} onHide={handleCloseUploadModal}>
        <Modal.Header closeButton>
          <Modal.Title>Upload CSV</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group controlId="formFile">
              <Form.Label>Choose CSV File</Form.Label>
              <Form.Control
                type="file"
                accept=".csv"
                onChange={(e) => setFile(e.target.files[0])}
                required
                aria-label="Choose CSV file"
              />
            </Form.Group>
            <Button variant="primary" onClick={uploadCSV} disabled={uploadLoading}>
              {uploadLoading ? <Spinner as="span" animation="border" size="sm" /> : 'Upload'}
            </Button>
          </Form>
        </Modal.Body>
      </Modal>
    </div>
  );
};

export default InceptionsPage;
