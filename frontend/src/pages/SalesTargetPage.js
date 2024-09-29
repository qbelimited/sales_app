import React, { useState, useEffect, useCallback } from 'react';
import { Modal, Button, Table, Pagination, Form } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEdit, faTrashAlt, faPlus } from '@fortawesome/free-solid-svg-icons';
import api from '../services/api';

const SalesTargetPage = ({ showToast }) => {
  const [salesTargets, setSalesTargets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentTarget, setCurrentTarget] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [targetToDelete, setTargetToDelete] = useState(null);
  const [showPastTargets, setShowPastTargets] = useState(false);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const itemsPerPage = 10;
  const [totalRunningTargets, setTotalRunningTargets] = useState(0);
  const [salesManagers, setSalesManagers] = useState([]);

  // Filter state
  const [selectedManager, setSelectedManager] = useState('');
  const [criteriaTypes, setCriteriaTypes] = useState([]);
  const [criteriaValues, setCriteriaValues] = useState([]);
  const [customCriteriaType, setCustomCriteriaType] = useState('');
  const [customCriteriaValue, setCustomCriteriaValue] = useState('');
  const [selectedCriteriaType, setSelectedCriteriaType] = useState('');
  const [selectedCriteriaValue, setSelectedCriteriaValue] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const local_user = JSON.parse(localStorage.getItem('user'));
  const role_id = parseInt(local_user?.role_id) || local_user?.role?.id;
  const userId = local_user?.id;

  const fetchSalesManagers = useCallback(async () => {
    try {
      const response = await api.get('/dropdown/', {
        params: { type: 'users_with_roles', role_id: 4 },
      });
      setSalesManagers(response.data);
    } catch (error) {
      console.error('Error fetching sales managers:', error);
      showToast('danger', 'Failed to fetch sales managers.', 'Error');
    }
  }, [showToast]);

  const fetchSalesTargets = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.get(`/sales_target/?sort_by=created_at&per_page=100&page=1`);
      const targets = Array.isArray(response.data.sales_targets) ? response.data.sales_targets : [];

      const filteredTargets = role_id === 4
        ? targets.filter(target => target.sales_manager_id === userId)
        : targets;

      const types = [...new Set(targets.map(target => target.target_criteria_type))];
      const values = [...new Set(targets.map(target => target.target_criteria_value))];
      setCriteriaTypes(types);
      setCriteriaValues(values);

      const additionalFilteredTargets = filteredTargets.filter(target => {
        const matchesManager = selectedManager ? target.sales_manager_id === selectedManager : true;
        const matchesCriteriaType = selectedCriteriaType ? target.target_criteria_type === selectedCriteriaType : true;
        const matchesCriteriaValue = selectedCriteriaValue ? target.target_criteria_value === selectedCriteriaValue : true;
        const matchesDate = (startDate && endDate) ?
          new Date(target.period_start) >= new Date(startDate) && new Date(target.period_end) <= new Date(endDate) : true;

        return matchesManager && matchesCriteriaType && matchesCriteriaValue && matchesDate;
      });

      setSalesTargets(additionalFilteredTargets);
      setTotalPages(Math.ceil(additionalFilteredTargets.length / itemsPerPage));
      setTotalRunningTargets(additionalFilteredTargets.length);
    } catch (err) {
      console.error('Error fetching sales targets:', err);
      setError('Failed to load sales targets.');
    } finally {
      setLoading(false);
    }
  }, [role_id, userId, selectedManager, selectedCriteriaType, selectedCriteriaValue, startDate, endDate, itemsPerPage]);

  useEffect(() => {
    fetchSalesManagers();
    fetchSalesTargets();
  }, [fetchSalesManagers, fetchSalesTargets]);

  const handleShowAddModal = () => {
    setCurrentTarget(null); // Reset current target for add
    setShowAddModal(true);
    setCustomCriteriaType(''); // Reset custom input
    setCustomCriteriaValue(''); // Reset custom input
  };

  const handleCloseAddModal = () => {
    setShowAddModal(false);
    setCustomCriteriaType(''); // Reset custom input
    setCustomCriteriaValue(''); // Reset custom input
  };

  const handleShowEditModal = (target) => {
    setCurrentTarget(target);
    setShowEditModal(true);
    setCustomCriteriaType(''); // Reset custom input
    setCustomCriteriaValue(''); // Reset custom input
  };

  const handleCloseEditModal = () => {
    setCurrentTarget(null);
    setShowEditModal(false);
    setCustomCriteriaType(''); // Reset custom input
    setCustomCriteriaValue(''); // Reset custom input
  };

  const handleShowDeleteModal = (target) => {
    setTargetToDelete(target);
    setShowDeleteModal(true);
  };

  const handleCloseDeleteModal = () => {
    setTargetToDelete(null);
    setShowDeleteModal(false);
  };

  const addSalesTarget = async (targetData) => {
    try {
      await api.post('/sales_target/', targetData);
      showToast('success', 'Sales target created successfully.', 'Success');
    } catch (err) {
      console.error('Error adding sales target:', err);
      showToast('danger', 'Failed to save sales target.', 'Error');
    }
  };

  const editSalesTarget = async (targetData) => {
    try {
      await api.put(`/sales_target/${currentTarget.id}`, targetData);
      showToast('success', 'Sales target updated successfully.', 'Success');
    } catch (err) {
      console.error('Error updating sales target:', err);
      showToast('danger', 'Failed to save sales target.', 'Error');
    }
  };

  const handleSubmit = async (e, isEditing) => {
    e.preventDefault();
    const formData = new FormData(e.target);

    // Prepare datetime objects with time set to 12:00 AM
    const periodStartDate = new Date(formData.get('period_start'));
    periodStartDate.setHours(0, 0, 0); // Set to 12:00 AM

    const periodEndDate = new Date(formData.get('period_end'));
    periodEndDate.setHours(0, 0, 0); // Set to 12:00 AM

    const targetData = {
      sales_manager_id: parseInt(formData.get('sales_manager_id'), 10), // Convert to integer
      target_sales_count: Math.round(Number(formData.get('target_sales_count'))), // Ensure it's a whole number
      target_premium_amount: parseFloat(formData.get('target_premium_amount')), // Convert to float
      target_criteria_type: customCriteriaType || formData.get('target_criteria_type'),
      target_criteria_value: customCriteriaValue || formData.get('target_criteria_value'),
      period_start: periodStartDate.toISOString(), // Convert to ISO string
      period_end: periodEndDate.toISOString(), // Convert to ISO string
      is_active: true
    };

    if (isEditing) {
      await editSalesTarget(targetData);
    } else {
      await addSalesTarget(targetData);
    }

    fetchSalesTargets();
    if (isEditing) handleCloseEditModal();
    else handleCloseAddModal();
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/sales_target/${targetToDelete.id}`);
      showToast('success', 'Sales target deleted successfully.', 'Success');
      fetchSalesTargets();
      handleCloseDeleteModal();
    } catch (err) {
      console.error('Error deleting sales target:', err);
      showToast('danger', 'Failed to delete sales target.', 'Error');
    }
  };

  const activeTargets = salesTargets.filter(target => target.is_active);
  const pastTargets = salesTargets.filter(target => !target.is_active);
  const paginatedTargets = activeTargets.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  return (
    <div className="container mt-5">
      <h1 className="text-center mb-4">Manage Sales Targets</h1>
      {loading && <p>Loading sales targets...</p>}
      {error && <p className="text-danger">{error}</p>}

      <div className="d-flex justify-content-between align-items-center mb-3">
        {(role_id === 3 || role_id === 2) && (
          <Button variant="primary" onClick={handleShowAddModal}>
            <FontAwesomeIcon icon={faPlus} /> Add Sales Target
          </Button>
        )}
        <div className="d-flex flex-wrap align-items-center">
          <Form.Control as="select" value={selectedManager} onChange={(e) => setSelectedManager(e.target.value)} className="me-1" style={{ width: '150px' }}>
            <option value="">Manager</option>
            {salesManagers.map(manager => (
              <option key={manager.id} value={manager.id}>{manager.name}</option>
            ))}
          </Form.Control>
          <Form.Control as="select" value={selectedCriteriaType} onChange={(e) => setSelectedCriteriaType(e.target.value)} className="me-1" style={{ width: '150px' }}>
            <option value="">Criteria Type</option>
            {criteriaTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </Form.Control>
          <Form.Control as="select" value={selectedCriteriaValue} onChange={(e) => setSelectedCriteriaValue(e.target.value)} className="me-1" style={{ width: '150px' }}>
            <option value="">Criteria Value</option>
            {criteriaValues.map(value => (
              <option key={value} value={value}>{value}</option>
            ))}
          </Form.Control>
          <Form.Control type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="me-1" style={{ width: '120px' }} />
          <Form.Control type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="me-1" style={{ width: '120px' }} />
          <Button variant="primary" onClick={fetchSalesTargets}>Apply</Button>
        </div>
      </div>

      <Button
        variant={showPastTargets ? 'primary' : 'secondary'}
        onClick={() => setShowPastTargets(!showPastTargets)}
        className="mb-3"
      >
        {showPastTargets ? 'Hide Past Targets' : 'Show Past Targets'}
      </Button>

      <div className="mt-3">
        <h5>Total Running Targets: {totalRunningTargets}</h5>
      </div>

      <Table striped bordered hover responsive className="mt-3">
        <thead>
          <tr>
            <th>Sales Manager</th>
            <th>Target Sales Count</th>
            <th>Target Premium Amount</th>
            <th>Criteria Type</th>
            <th>Criteria Value</th>
            <th>Period Start</th>
            <th>Period End</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {paginatedTargets.map(target => (
            <tr key={target.id}>
              <td>{salesManagers.find(manager => manager.id === target.sales_manager_id)?.name || target.sales_manager_id}</td>
              <td>{Math.round(target.target_sales_count)}</td>
              <td>{parseFloat(target.target_premium_amount).toFixed(2)}</td>
              <td>{target.target_criteria_type}</td>
              <td>{target.target_criteria_value}</td>
              <td>{new Date(target.period_start).toLocaleString()}</td>
              <td>{new Date(target.period_end).toLocaleString()}</td>
              <td>
                {(role_id === 3 || role_id === 2) && (
                  <>
                    <Button variant="warning" onClick={() => handleShowEditModal(target)}>
                      <FontAwesomeIcon icon={faEdit} /> Edit
                    </Button>
                    <Button variant="danger" onClick={() => handleShowDeleteModal(target)}>
                      <FontAwesomeIcon icon={faTrashAlt} /> Delete
                    </Button>
                  </>
                )}
              </td>
            </tr>
          ))}
          {showPastTargets && pastTargets.map(target => (
            <tr key={target.id} className="table-secondary">
              <td>{salesManagers.find(manager => manager.id === target.sales_manager_id)?.name || target.sales_manager_id}</td>
              <td>{Math.round(target.target_sales_count)}</td>
              <td>{parseFloat(target.target_premium_amount).toFixed(2)}</td>
              <td>{target.target_criteria_type}</td>
              <td>{target.target_criteria_value}</td>
              <td>{new Date(target.period_start).toLocaleString()}</td>
              <td>{new Date(target.period_end).toLocaleString()}</td>
              <td>
                {(role_id === 3 || role_id === 2) && (
                  <>
                    <Button variant="warning" onClick={() => handleShowEditModal(target)}>
                      <FontAwesomeIcon icon={faEdit} /> Edit
                    </Button>
                    <Button variant="danger" onClick={() => handleShowDeleteModal(target)}>
                      <FontAwesomeIcon icon={faTrashAlt} /> Delete
                    </Button>
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      {/* Pagination Controls */}
      <Pagination className="justify-content-center mt-3">
        <Pagination.Prev onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))} disabled={currentPage === 1} />
        {Array.from({ length: Math.min(5, totalPages) }, (_, index) => {
          const pageNum = index + 1 + Math.max(0, currentPage - 3);
          if (pageNum <= totalPages) {
            return (
              <Pagination.Item key={pageNum} active={pageNum === currentPage} onClick={() => setCurrentPage(pageNum)}>
                {pageNum}
              </Pagination.Item>
            );
          }
          return null;
        })}
        <Pagination.Next onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))} disabled={currentPage === totalPages} />
      </Pagination>

      {/* Modal for adding sales target */}
      <Modal show={showAddModal} onHide={handleCloseAddModal}>
        <Modal.Header closeButton>
          <Modal.Title>Add Sales Target</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <form onSubmit={(e) => handleSubmit(e, false)}>
            <div className="mb-3">
              <label htmlFor="sales_manager_id" className="form-label">Sales Manager</label>
              <select name="sales_manager_id" className="form-control" required>
                <option value="">Select Manager</option>
                {salesManagers.map(manager => (
                  <option key={manager.id} value={manager.id}>
                    {manager.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="mb-3">
              <label htmlFor="target_sales_count" className="form-label">Target Sales Count</label>
              <input type="number" name="target_sales_count" className="form-control" required />
            </div>
            <div className="mb-3">
              <label htmlFor="target_premium_amount" className="form-label">Target Premium Amount</label>
              <input type="number" name="target_premium_amount" className="form-control" required />
            </div>
            <div className="mb-3">
              <label htmlFor="target_criteria_type" className="form-label">Target Criteria Type</label>
              <select name="target_criteria_type" className="form-control" required onChange={(e) => {
                const value = e.target.value;
                setCustomCriteriaType(value === 'custom' ? '' : customCriteriaType);
              }}>
                <option value="">Select Criteria Type</option>
                {criteriaTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
                <option value="custom">Other (Input below)</option>
              </select>
              {customCriteriaType === '' && (
                <input type="text" className="form-control mt-2" placeholder="Enter custom criteria type" onChange={(e) => setCustomCriteriaType(e.target.value)} />
              )}
            </div>
            <div className="mb-3">
              <label htmlFor="target_criteria_value" className="form-label">Target Criteria Value</label>
              <select name="target_criteria_value" className="form-control" required onChange={(e) => {
                const value = e.target.value;
                setCustomCriteriaValue(value === 'custom' ? '' : customCriteriaValue);
              }}>
                <option value="">Select Criteria Value</option>
                {criteriaValues.map(value => (
                  <option key={value} value={value}>{value}</option>
                ))}
                <option value="custom">Other (Input below)</option>
              </select>
              {customCriteriaValue === '' && (
                <input type="text" className="form-control mt-2" placeholder="Enter custom criteria value" onChange={(e) => setCustomCriteriaValue(e.target.value)} />
              )}
            </div>
            <div className="mb-3">
              <label htmlFor="period_start" className="form-label">Period Start</label>
              <input type="datetime-local" name="period_start" className="form-control" required />
            </div>
            <div className="mb-3">
              <label htmlFor="period_end" className="form-label">Period End</label>
              <input type="datetime-local" name="period_end" className="form-control" required />
            </div>
            <Button variant="primary" type="submit">
              Create Target
            </Button>
          </form>
        </Modal.Body>
      </Modal>

      {/* Modal for editing sales target */}
      <Modal show={showEditModal} onHide={handleCloseEditModal}>
        <Modal.Header closeButton>
          <Modal.Title>Edit Sales Target</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <form onSubmit={(e) => handleSubmit(e, true)}>
            <input type="hidden" name="id" defaultValue={currentTarget ? currentTarget.id : ''} />
            <div className="mb-3">
              <label htmlFor="sales_manager_id" className="form-label">Sales Manager</label>
              <select name="sales_manager_id" className="form-control" defaultValue={currentTarget ? currentTarget.sales_manager_id : ''} required>
                <option value="">Select Manager</option>
                {salesManagers.map(manager => (
                  <option key={manager.id} value={manager.id}>
                    {manager.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="mb-3">
              <label htmlFor="target_sales_count" className="form-label">Target Sales Count</label>
              <input type="number" name="target_sales_count" className="form-control" defaultValue={currentTarget ? currentTarget.target_sales_count : ''} required />
            </div>
            <div className="mb-3">
              <label htmlFor="target_premium_amount" className="form-label">Target Premium Amount</label>
              <input type="number" name="target_premium_amount" className="form-control" defaultValue={currentTarget ? currentTarget.target_premium_amount : ''} required />
            </div>
            <div className="mb-3">
              <label htmlFor="target_criteria_type" className="form-label">Target Criteria Type</label>
              <select name="target_criteria_type" className="form-control" defaultValue={currentTarget ? currentTarget.target_criteria_type : ''} required>
                <option value="">Select Criteria Type</option>
                {criteriaTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
            <div className="mb-3">
              <label htmlFor="target_criteria_value" className="form-label">Target Criteria Value</label>
              <select name="target_criteria_value" className="form-control" defaultValue={currentTarget ? currentTarget.target_criteria_value : ''} required>
                <option value="">Select Criteria Value</option>
                {criteriaValues.map(value => (
                  <option key={value} value={value}>{value}</option>
                ))}
              </select>
            </div>
            <div className="mb-3">
              <label htmlFor="period_start" className="form-label">Period Start</label>
              <input type="datetime-local" name="period_start" className="form-control" defaultValue={currentTarget ? currentTarget.period_start : ''} required />
            </div>
            <div className="mb-3">
              <label htmlFor="period_end" className="form-label">Period End</label>
              <input type="datetime-local" name="period_end" className="form-control" defaultValue={currentTarget ? currentTarget.period_end : ''} required />
            </div>
            <Button variant="primary" type="submit">
              Update Target
            </Button>
          </form>
        </Modal.Body>
      </Modal>

      {/* Modal for delete confirmation */}
      <Modal show={showDeleteModal} onHide={handleCloseDeleteModal}>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Deletion</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>Are you sure you want to delete this sales target? This action cannot be undone.</p>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseDeleteModal}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleDelete}>
            Delete
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default SalesTargetPage;
