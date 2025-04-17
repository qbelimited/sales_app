import React, { useState, useEffect, useCallback } from 'react';
import { Spinner, Button, Form, Modal, Table, Alert } from 'react-bootstrap';
import api from '../services/api';

const RetentionPolicyPage = ({ showToast }) => {
  const [retentionPolicies, setRetentionPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState(null);
  const [dataTypes, setDataTypes] = useState([]);
  const [importanceLevels, setImportanceLevels] = useState([]);
  const [volumeStats, setVolumeStats] = useState({});

  // Form state
  const [formData, setFormData] = useState({
    data_type: '',
    importance: '',
    retention_days: '',
    archive_before_delete: true,
    max_retention_days: '',
    notification_days: ''
  });

  // Fetch retention policies and types
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [policiesResponse, typesResponse] = await Promise.all([
        api.get('/retention/'),
        api.get('/retention/types')
      ]);

      setRetentionPolicies(policiesResponse.data);
      setDataTypes(typesResponse.data.data_types);
      setImportanceLevels(typesResponse.data.importance_levels);

      // Fetch volume stats for each policy
      const stats = {};
      for (const policy of policiesResponse.data) {
        const volumeResponse = await api.get(`/retention/volume/${policy.data_type}`);
        stats[policy.data_type] = volumeResponse.data;
      }
      setVolumeStats(stats);
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Failed to fetch data. Please try again later.');
      showToast('danger', 'Failed to fetch data. Please try again later.', 'Error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Handle form input changes
  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  // Handle edit button click
  const handleEdit = (policy) => {
    setSelectedPolicy(policy);
    setFormData({
      data_type: policy.data_type,
      importance: policy.importance,
      retention_days: policy.retention_days,
      archive_before_delete: policy.archive_before_delete,
      max_retention_days: policy.max_retention_days || '',
      notification_days: policy.notification_days || ''
    });
    setShowModal(true);
  };

  // Handle form submission
  const handleSubmit = async () => {
    try {
      const data = {
        ...formData,
        retention_days: parseInt(formData.retention_days, 10),
        max_retention_days: formData.max_retention_days ? parseInt(formData.max_retention_days, 10) : null,
        notification_days: formData.notification_days ? parseInt(formData.notification_days, 10) : null
      };

      await api.put('/retention/', data);
      showToast('success', 'Retention policy updated successfully!', 'Success');
      fetchData();
      setShowModal(false);
    } catch (error) {
      console.error('Error updating retention policy:', error);
      showToast('danger', 'Failed to update retention policy. Please try again.', 'Error');
    }
  };

  if (loading) return <Spinner animation="border" />;

  return (
    <div style={{ marginTop: '20px', padding: '20px' }}>
      <h2>Data Retention Policies</h2>
      {error && <Alert variant="danger">{error}</Alert>}

      <Table striped bordered hover>
        <thead>
          <tr>
            <th>Data Type</th>
            <th>Importance</th>
            <th>Retention Days</th>
            <th>Archive Before Delete</th>
            <th>Max Retention Days</th>
            <th>Notification Days</th>
            <th>Total Records</th>
            <th>Expiring Records</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {retentionPolicies.map(policy => (
            <tr key={policy.id}>
              <td>{policy.data_type}</td>
              <td>{policy.importance}</td>
              <td>{policy.retention_days}</td>
              <td>{policy.archive_before_delete ? 'Yes' : 'No'}</td>
              <td>{policy.max_retention_days || '-'}</td>
              <td>{policy.notification_days || '-'}</td>
              <td>{volumeStats[policy.data_type]?.total_records || 0}</td>
              <td>{volumeStats[policy.data_type]?.expiring_records || 0}</td>
              <td>
                <Button variant="primary" size="sm" onClick={() => handleEdit(policy)}>
                  Edit
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      {/* Edit Policy Modal */}
      <Modal show={showModal} onHide={() => setShowModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Edit Retention Policy</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group>
              <Form.Label>Data Type</Form.Label>
              <Form.Control
                as="select"
                name="data_type"
                value={formData.data_type}
                onChange={handleInputChange}
                disabled={!!selectedPolicy}
              >
                {dataTypes.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </Form.Control>
            </Form.Group>

            <Form.Group>
              <Form.Label>Importance Level</Form.Label>
              <Form.Control
                as="select"
                name="importance"
                value={formData.importance}
                onChange={handleInputChange}
              >
                {importanceLevels.map(level => (
                  <option key={level.value} value={level.value}>
                    {level.label}
                  </option>
                ))}
              </Form.Control>
            </Form.Group>

            <Form.Group>
              <Form.Label>Retention Days</Form.Label>
              <Form.Control
                type="number"
                name="retention_days"
                value={formData.retention_days}
                onChange={handleInputChange}
                min="1"
              />
            </Form.Group>

            <Form.Group>
              <Form.Label>Max Retention Days (Optional)</Form.Label>
              <Form.Control
                type="number"
                name="max_retention_days"
                value={formData.max_retention_days}
                onChange={handleInputChange}
                min="1"
              />
            </Form.Group>

            <Form.Group>
              <Form.Label>Notification Days (Optional)</Form.Label>
              <Form.Control
                type="number"
                name="notification_days"
                value={formData.notification_days}
                onChange={handleInputChange}
                min="1"
              />
            </Form.Group>

            <Form.Group>
              <Form.Check
                type="checkbox"
                label="Archive Before Delete"
                name="archive_before_delete"
                checked={formData.archive_before_delete}
                onChange={handleInputChange}
              />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModal(false)}>
            Close
          </Button>
          <Button variant="primary" onClick={handleSubmit}>
            Save Changes
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default RetentionPolicyPage;
