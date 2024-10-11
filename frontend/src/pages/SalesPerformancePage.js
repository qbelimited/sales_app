import React, { useState, useEffect, useCallback } from 'react';
import { Modal, Button, Table, Spinner, Form, Row, Col } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEdit, faTrashAlt, faPlus, faInfoCircle } from '@fortawesome/free-solid-svg-icons';
import api from '../services/api';

const SalesPerformancePage = ({ showToast }) => {
  const [performanceData, setPerformanceData] = useState([]);
  const [salesManagers, setSalesManagers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPerformance, setCurrentPerformance] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showTargetDetailsModal, setShowTargetDetailsModal] = useState(false);
  const [targetDetails, setTargetDetails] = useState(null); // State to hold target details

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [itemsPerPage] = useState(10);

  // Filter state
  const [criteriaType, setCriteriaType] = useState('');
  const [criteriaValue, setCriteriaValue] = useState('');
  const [targetId, setTargetId] = useState('');

  const fetchSalesManagers = useCallback(async () => {
    try {
      const response = await api.get('/dropdown/', {
        params: { type: 'users_with_roles', role_id: 4 }, // Fetch users with role_id 4 (sales managers)
      });
      setSalesManagers(response.data);
    } catch (error) {
      console.error('Failed to fetch sales managers:', error);
    }
  }, []);

  const fetchPerformanceData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/sales_performance/', {
        params: {
          per_page: itemsPerPage,
          page: currentPage,
          criteria_type: criteriaType,
          criteria_value: criteriaValue,
          target_id: targetId,
        },
      });
      const performances = response.data.sales_performances;

      // Fetch target details for each unique target_id in performances
      const uniqueTargetIds = [...new Set(performances.map(performance => performance.target_id))];
      const targetDetailsPromises = uniqueTargetIds.map(async (id) => {
        try {
          const response = await api.get(`/sales_target/${id}`); // Fetch target details
          return response.data; // Return target details
        } catch (error) {
          console.error('Failed to fetch target details:', error);
          showToast('danger', 'Failed to fetch target details.', 'Error');
          return null; // Return null if error occurs
        }
      });
      const targetDetailsArray = await Promise.all(targetDetailsPromises);

      // Map target details to target IDs
      const targetDetailsMap = targetDetailsArray.reduce((acc, target) => {
        if (target) {
          acc[target.id] = target;
        }
        return acc;
      }, {});

      setPerformanceData(performances);
      setTotalPages(Math.ceil(response.data.total / itemsPerPage));
      return targetDetailsMap; // Return target details map for later use
    } catch (err) {
      console.error('Error fetching sales performance:', err);
      const errorMessage = err.response?.data?.message || 'Failed to load sales performance data.';
      setError(errorMessage);
      showToast('danger', errorMessage, 'Error');
    } finally {
      setLoading(false);
    }
  }, [showToast, currentPage, itemsPerPage, criteriaType, criteriaValue, targetId]);

  useEffect(() => {
    fetchSalesManagers();
    const loadData = async () => {
      const targetDetailsMap = await fetchPerformanceData();
      setTargetDetails(targetDetailsMap);
    };
    loadData();
  }, [fetchSalesManagers, fetchPerformanceData]);

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

  const handleShowTargetDetailsModal = (targetId) => {
    const target = targetDetails?.[targetId]; // Get specific target details
    if (target) {
      setTargetDetails(target); // Set target details for the modal
      setShowTargetDetailsModal(true);
    } else {
      console.error('Target not found for ID:', targetId);
      showToast('danger', 'Target details not found.', 'Error');
    }
  };

  const handleCloseTargetDetailsModal = () => {
    setShowTargetDetailsModal(false);
    setTargetDetails(null); // Clear target details when closing
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
      sales_manager_id: formData.get('sales_manager_id'),
      actual_sales_count: 0, // Adjust this value accordingly
      actual_premium_amount: 0, // Adjust this value accordingly
      target_id: formData.get('target_id'),
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

  // Calculate the number of working days between two dates
  const calculateWorkingDays = (startDate, endDate) => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    let count = 0;

    while (start <= end) {
      const day = start.getDay();
      if (day !== 0 && day !== 6) { // Exclude Sundays (0) and Saturdays (6)
        count++;
      }
      start.setDate(start.getDate() + 1);
    }

    return count;
  };

  const enhancedPerformanceData = performanceData.map(performance => {
    const target = targetDetails?.[performance.target_id]; // Get target details for calculations
    const targetSalesCount = target?.target_sales_count || 1; // Avoid division by zero
    const targetPremiumAmount = target?.target_premium_amount || 1; // Avoid division by zero
    const workingDays = target ? calculateWorkingDays(target.period_start, target.period_end) : 1; // Avoid division by zero

    return {
      ...performance,
      salesCountPercentage: ((performance.actual_sales_count / targetSalesCount) * 100).toFixed(2),
      premiumAmountPercentage: ((performance.actual_premium_amount / targetPremiumAmount) * 100).toFixed(2),
      criteriaMetCountPercentage: ((performance.criteria_met_count / workingDays) * 100).toFixed(2),
    };
  });

  // Pagination handlers
  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(prevPage => prevPage + 1);
    }
  };

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      setCurrentPage(prevPage => prevPage - 1);
    }
  };

  const handleFilter = (e) => {
    e.preventDefault();
    setCurrentPage(1); // Reset to first page on filter
    fetchPerformanceData(); // Fetch data with current filters
  };

  return (
    <div className="container mt-5">
      <h1 className="text-center mb-4">Sales Performance</h1>
      {loading && <Spinner animation="border" variant="primary" />}
      {error && <p className="text-danger">{error}</p>}

      <Row className="mb-3">
        <Col xs={12} md={3}>
          <Form.Control
            type="text"
            placeholder="Criteria Type"
            value={criteriaType}
            onChange={(e) => setCriteriaType(e.target.value)}
          />
        </Col>
        <Col xs={12} md={3}>
          <Form.Control
            type="text"
            placeholder="Criteria Value"
            value={criteriaValue}
            onChange={(e) => setCriteriaValue(e.target.value)}
          />
        </Col>
        <Col xs={12} md={3}>
          <Form.Control
            type="text"
            placeholder="Target ID"
            value={targetId}
            onChange={(e) => setTargetId(e.target.value)}
          />
        </Col>
        <Col xs={12} md={3}>
          <Button variant="primary" onClick={handleFilter}>
            Filter
          </Button>
        </Col>
      </Row>

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
            <th>Sales Manager</th>
            <th>Actual Sales Count</th>
            <th>% Sales Count</th>
            <th>Actual Premium Amount</th>
            <th>% Premium Amount</th>
            <th>Target</th>
            <th>Criteria Type</th>
            <th>Criteria Value</th>
            <th>Criteria Met Count</th>
            <th>% Criteria Met Count</th>
            <th>Performance Date</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {enhancedPerformanceData.map(performance => (
            <tr key={performance.id}>
              <td>{performance.id}</td>
              <td>{salesManagers.find(manager => manager.id === performance.sales_manager_id)?.name}</td>
              <td>{performance.actual_sales_count}</td>
              <td>{performance.salesCountPercentage}%</td>
              <td>{performance.actual_premium_amount}</td>
              <td>{performance.premiumAmountPercentage}%</td>
              <td>
                <Button variant="link" onClick={() => handleShowTargetDetailsModal(performance.target_id)}>
                  {performance.target_id} <FontAwesomeIcon icon={faInfoCircle} />
                </Button>
              </td>
              <td>{performance.criteria_type}</td>
              <td>{performance.criteria_value}</td>
              <td>{performance.criteria_met_count}</td>
              <td>{performance.criteriaMetCountPercentage}%</td>
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

      {/* Pagination Controls */}
      <div className="d-flex justify-content-center mt-4">
        <Button variant="secondary" onClick={handlePreviousPage} disabled={currentPage === 1}>
          Previous
        </Button>
        <span className="mx-2">{`Page ${currentPage} of ${totalPages}`}</span>
        <Button variant="secondary" onClick={handleNextPage} disabled={currentPage === totalPages}>
          Next
        </Button>
      </div>

      {/* Add Performance Modal */}
      <Modal show={showAddModal} onHide={handleCloseAddModal}>
        <Modal.Header closeButton>
          <Modal.Title>Add Performance</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form onSubmit={handleSubmit}>
            <Form.Group controlId="formSalesManager">
              <Form.Label>Sales Manager</Form.Label>
              <Form.Control as="select" name="sales_manager_id" required>
                <option value="">Select Sales Manager</option>
                {salesManagers.map(manager => (
                  <option key={manager.id} value={manager.id}>{manager.name}</option>
                ))}
              </Form.Control>
            </Form.Group>
            <Form.Group controlId="formTargetId">
              <Form.Label>Target ID</Form.Label>
              <Form.Control type="text" name="target_id" required />
            </Form.Group>
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
              <Form.Group controlId="formSalesManager">
                <Form.Label>Sales Manager</Form.Label>
                <Form.Control as="select" name="sales_manager_id" defaultValue={currentPerformance.sales_manager_id} required>
                  <option value="">Select Sales Manager</option>
                  {salesManagers.map(manager => (
                    <option key={manager.id} value={manager.id}>{manager.name}</option>
                  ))}
                </Form.Control>
              </Form.Group>
              <Form.Group controlId="formTargetId">
                <Form.Label>Target ID</Form.Label>
                <Form.Control type="text" name="target_id" defaultValue={currentPerformance.target_id} required />
              </Form.Group>
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

      {/* Target Details Modal */}
      <Modal show={showTargetDetailsModal} onHide={handleCloseTargetDetailsModal}>
        <Modal.Header closeButton>
          <Modal.Title>Target Details</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {targetDetails && (
            <div>
              <p><strong>ID:</strong> {targetDetails.id}</p>
              <p><strong>Target Sales Count:</strong> {targetDetails.target_sales_count}</p>
              <p><strong>Target Premium Amount:</strong> {targetDetails.target_premium_amount}</p>
              <p><strong>Criteria Type:</strong> {targetDetails.target_criteria_type}</p>
              <p><strong>Criteria Value:</strong> {targetDetails.target_criteria_value}</p>
              <p><strong>Period Start:</strong> {new Date(targetDetails.period_start).toLocaleDateString()}</p>
              <p><strong>Period End:</strong> {new Date(targetDetails.period_end).toLocaleDateString()}</p>
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseTargetDetailsModal}>Close</Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default SalesPerformancePage;
