import React, { useState, useEffect, useCallback } from 'react';
import { Spinner, Button, Form, Modal } from 'react-bootstrap';
import api from '../services/api';

const RetentionPolicyPage = ({ showToast }) => {
  const [retentionPolicy, setRetentionPolicy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [retentionDays, setRetentionDays] = useState(''); // Initialize as an empty string

  // Fetch the retention policy
  const fetchRetentionPolicy = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/retention/');
      setRetentionPolicy(response.data);
      setRetentionDays(response.data.retention_days || ''); // Set to empty string if undefined
    } catch (error) {
      console.error('Error fetching retention policy:', error);
      setError('Failed to fetch retention policy. Please try again later.');
      showToast('danger', 'Failed to fetch retention policy. Please try again later.', 'Error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchRetentionPolicy();
  }, [fetchRetentionPolicy]);

  // Update the retention policy
  const handleSaveRetention = async () => {
    if (isNaN(retentionDays) || retentionDays < 0) {
      showToast('warning', 'Please enter a valid number for retention days.', 'Warning');
      return;
    }

    try {
      await api.put('/retention/', {
        retention_days: parseInt(retentionDays, 10),
      });
      showToast('success', 'Retention policy updated successfully!', 'Success');
      fetchRetentionPolicy(); // Refresh the policy
      setShowModal(false);
    } catch (error) {
      console.error('Error updating retention policy:', error);
      showToast('danger', 'Failed to update retention policy. Please try again.', 'Error');
    }
  };

  if (loading) return <Spinner animation="border" />;

  return (
    <div style={{ marginTop: '20px', padding: '20px' }}>
      <h2>Data Retention Policy</h2>
      {error && <p className="text-danger">{error}</p>}
      {retentionPolicy && (
        <>
          <p><strong>Retention Days:</strong> {retentionPolicy.retention_days} days</p>
          <Button variant="primary" onClick={() => setShowModal(true)}>
            Update Retention Policy
          </Button>
        </>
      )}

      {/* Update Retention Policy Modal */}
      <Modal show={showModal} onHide={() => setShowModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Update Retention Policy</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group>
              <Form.Label>Retention Days</Form.Label>
              <Form.Control
                type="number"
                value={retentionDays}
                onChange={(e) => setRetentionDays(e.target.value || '')} // Ensure it can be empty
                placeholder="Enter retention days"
              />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModal(false)}>
            Close
          </Button>
          <Button variant="primary" onClick={handleSaveRetention}>
            Save Changes
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default RetentionPolicyPage;
