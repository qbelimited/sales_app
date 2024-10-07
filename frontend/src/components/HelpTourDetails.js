import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import { Modal, Button } from 'react-bootstrap';
import Loading from '../components/Loading';

const HelpTourDetails = ({ userId, onClose, showToast }) => {
  const [steps, setSteps] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchTourSteps = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get(`/help/tours/${userId}/steps`);
      setSteps(response.data);
    } catch (error) {
      console.error('Error fetching tour steps:', error);
      showToast('danger', 'Failed to fetch tour steps.', 'Error');
    } finally {
      setLoading(false);
    }
  }, [userId, showToast]);

  useEffect(() => {
    fetchTourSteps();
  }, [fetchTourSteps]);

  return (
    <Modal show onHide={onClose} centered>
      <Modal.Header closeButton>
        <Modal.Title>User {userId} - Tour Steps</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {loading ? (
          <Loading />
        ) : (
          <ul>
            {steps.map((step) => (
              <li key={step.id}>
                <strong>{step.page_name}</strong>: {step.content}
              </li>
            ))}
          </ul>
        )}
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onClose}>Close</Button>
      </Modal.Footer>
    </Modal>
  );
};

export default HelpTourDetails;
