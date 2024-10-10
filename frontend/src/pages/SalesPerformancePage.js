import React, { useState, useEffect, useCallback } from 'react';
import { Modal, Button, Table, Spinner, Form } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEdit, faTrashAlt, faPlus } from '@fortawesome/free-solid-svg-icons';
import api from '../services/api';

const SalesPerformancePage = ({ showToast }) => {
  const [performanceData, setPerformanceData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPerformance, setCurrentPerformance] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const fetchPerformanceData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/sales_performance/');
      setPerformanceData(response.data.sales_performances);
    } catch (err) {
      console.error('Error fetching sales performance:', err);
      setError('Failed to load sales performance data.');
      showToast('danger', 'Failed to load sales performance data.', 'Error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchPerformanceData();
  }, [fetchPerformanceData]);

  const handleShowAddModal = () => {
    setCurrentPerformance(null);
    setShowAddModal(true);
  };

  const handleCloseAddModal = () => {
    setShowAddModal(false);
  };

  const handleShowEditModal = (performance) => {
    setCurrentPerformance(performance);
    setShowEditModal(true);
  };

  const handleCloseEditModal = () => {
    setCurrentPerformance(null);
    setShowEditModal(false);
  };

  const handleShowDeleteModal = (performance) => {
    setCurrentPerformance(performance);
    setShowDeleteModal(true);
  };

  const handleCloseDeleteModal = () => {
    setCurrentPerformance(null);
    setShowDeleteModal(false);
  };

  const addPerformance = async (data) => {
    try {
      await api.post('/sales_performance/', data);
      showToast('success', 'Performance created successfully.', 'Success');
      fetchPerformanceData();
      handleCloseAddModal();
    } catch (err) {
      console.error('Error adding performance:', err);
      showToast('danger', 'Failed to save performance.', 'Error');
    }
  };

  const editPerformance = async (data) => {
    try {
      await api.put(`/sales_performance/${currentPerformance.id}`, data);
      showToast('success', 'Performance updated successfully.', 'Success');
      fetchPerformanceData();
      handleCloseEditModal();
    } catch (err) {
      console.error('Error updating performance:', err);
      showToast('danger', 'Failed to update performance.', 'Error');
    }
  };

  const deletePerformance = async () => {
    try {
      await api.delete(`/sales_performance/${currentPerformance.id}`);
      showToast('success', 'Performance deleted successfully.', 'Success');
      fetchPerformanceData();
      handleCloseDeleteModal();
    } catch (err) {
      console.error('Error deleting performance:', err);
      showToast('danger', 'Failed to delete performance.', 'Error');
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
      sales_manager_id: 0, // Replace with actual sales manager ID
      actual_sales_count: 0, // Adjust this value accordingly
      actual_premium_amount: 0, // Adjust this value accordingly
      target_id: 0, // Replace with actual target ID
      criteria_type: formData.get('criteria_type'),
      criteria_value: formData.get('criteria_value'),
      criteria_met_count: 0, // Adjust this value accordingly
      performance_date: formData.get('performance_date'),
    };

    if (currentPerformance) {
      editPerformance(data);
    } else {
      addPerformance(data);
    }
  };

  const generatePerformanceRecords = async () => {
    try {
      await api.post('/sales_performance/auto-generate');
      showToast('success', 'Performance records generated successfully.', 'Success');
      fetchPerformanceData();
    } catch (err) {
      console.error('Error generating performance records:', err);
      showToast('danger', 'Failed to generate performance records.', 'Error');
    }
  };

  const updatePerformanceRecords = async () => {
    try {
      await api.post('/sales_performance/auto-update');
      showToast('success', 'Performance records updated successfully.', 'Success');
      fetchPerformanceData();
    } catch (err) {
      console.error('Error updating performance records:', err);
      showToast('danger', 'Failed to update performance records.', 'Error');
    }
  };

  return (
    <div className="container mt-5">
      <h1 className="text-center mb-4">Sales Performance</h1>
      {loading && <Spinner animation="border" variant="primary" />}
      {error && <p className="text-danger">{error}</p>}

      <Button variant="primary" onClick={handleShowAddModal} className="mb-3">
        <FontAwesomeIcon icon={faPlus} /> Add Performance
      </Button>
      <Button variant="success" onClick={generatePerformanceRecords} className="mb-3 ml-2">
        Generate Past Performances
      </Button>
      <Button variant="info" onClick={updatePerformanceRecords} className="mb-3 ml-2">
        Update Performances
      </Button>

      <Table striped bordered hover responsive className="mt-3">
        <thead>
          <tr>
            <th>ID</th>
            <th>Sales Manager ID</th>
            <th>Actual Sales Count</th>
            <th>Actual Premium Amount</th>
            <th>Target ID</th>
            <th>Criteria Type</th>
            <th>Criteria Value</th>
            <th>Criteria Met Count</th>
            <th>Performance Date</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {performanceData.map(performance => (
            <tr key={performance.id}>
              <td>{performance.id}</td>
              <td>{performance.sales_manager_id}</td>
              <td>{performance.actual_sales_count}</td>
              <td>{performance.actual_premium_amount}</td>
              <td>{performance.target_id}</td>
              <td>{performance.criteria_type}</td>
              <td>{performance.criteria_value}</td>
              <td>{performance.criteria_met_count}</td>
              <td>{new Date(performance.performance_date).toLocaleDateString()}</td>
              <td>
                <Button variant="warning" onClick={() => handleShowEditModal(performance)}>
                  <FontAwesomeIcon icon={faEdit} /> Edit
                </Button>
                <Button variant="danger" onClick={() => handleShowDeleteModal(performance)}>
                  <FontAwesomeIcon icon={faTrashAlt} /> Delete
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      {/* Add Performance Modal */}
      <Modal show={showAddModal} onHide={handleCloseAddModal}>
        <Modal.Header closeButton>
          <Modal.Title>Add Performance</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form onSubmit={handleSubmit}>
            <Form.Group controlId="formCriteriaType">
              <Form.Label>Criteria Type</Form.Label>
              <Form.Control type="text" name="criteria_type" required />
            </Form.Group>
            <Form.Group controlId="formCriteriaValue">
              <Form.Label>Criteria Value</Form.Label>
              <Form.Control type="text" name="criteria_value" required />
            </Form.Group>
            <Form.Group controlId="formPerformanceDate">
              <Form.Label>Performance Date</Form.Label>
              <Form.Control type="datetime-local" name="performance_date" required />
            </Form.Group>
            <Button variant="primary" type="submit">Create</Button>
          </Form>
        </Modal.Body>
      </Modal>

      {/* Edit Performance Modal */}
      <Modal show={showEditModal} onHide={handleCloseEditModal}>
        <Modal.Header closeButton>
          <Modal.Title>Edit Performance</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {currentPerformance && (
            <Form onSubmit={handleSubmit}>
              <Form.Group controlId="formCriteriaType">
                <Form.Label>Criteria Type</Form.Label>
                <Form.Control type="text" name="criteria_type" defaultValue={currentPerformance.criteria_type} required />
              </Form.Group>
              <Form.Group controlId="formCriteriaValue">
                <Form.Label>Criteria Value</Form.Label>
                <Form.Control type="text" name="criteria_value" defaultValue={currentPerformance.criteria_value} required />
              </Form.Group>
              <Form.Group controlId="formPerformanceDate">
                <Form.Label>Performance Date</Form.Label>
                <Form.Control type="datetime-local" name="performance_date" defaultValue={currentPerformance.performance_date.slice(0, 16)} required />
              </Form.Group>
              <Button variant="primary" type="submit">Update</Button>
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
          <p>Are you sure you want to delete this performance record? This action cannot be undone.</p>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseDeleteModal}>Cancel</Button>
          <Button variant="danger" onClick={deletePerformance}>Delete</Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default SalesPerformancePage;
