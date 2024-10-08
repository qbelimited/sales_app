import React, { useState, useEffect } from 'react';
import { Form, Button, Modal } from 'react-bootstrap';
import api from '../services/api';

const HelpStepForm = ({ step, fetchSteps, onHide, showToast }) => {
  const [stepData, setStepData] = useState({
    page_name: '',
    target: '',
    content: '',
    order: 0,
  });

  useEffect(() => {
    if (step) {
      setStepData({
        page_name: step.page_name,
        target: step.target,
        content: step.content,
        order: step.order,
      });
    }
  }, [step]);

  const handleSave = async () => {
    try {
      if (step) {
        // Update existing step
        await api.put(`/help/steps/${step.id}`, stepData);
        showToast('success', 'Step updated successfully.', 'Success');
      } else {
        // Add new step
        await api.post('/help/steps', stepData);
        showToast('success', 'Step added successfully.', 'Success');
      }
      fetchSteps(); // Refresh the list after add or edit
      onHide(); // Close the form
    } catch (error) {
      console.error('Error saving step:', error);
      showToast('danger', 'Failed to save step.', 'Error');
    }
  };

  return (
    <Modal show onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title>{step ? 'Edit Step' : 'Add Step'}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Form>
          <Form.Group controlId="formPageName">
            <Form.Label>Page Name</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter Page Name"
              value={stepData.page_name}
              onChange={(e) => setStepData({ ...stepData, page_name: e.target.value })}
              required
            />
          </Form.Group>
          <Form.Group controlId="formTarget">
            <Form.Label>Target</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter Target"
              value={stepData.target}
              onChange={(e) => setStepData({ ...stepData, target: e.target.value })}
              required
            />
          </Form.Group>
          <Form.Group controlId="formContent">
            <Form.Label>Content</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              placeholder="Enter Content"
              value={stepData.content}
              onChange={(e) => setStepData({ ...stepData, content: e.target.value })}
              required
            />
          </Form.Group>
          <Form.Group controlId="formOrder">
            <Form.Label>Order</Form.Label>
            <Form.Control
              type="number"
              value={stepData.order}
              onChange={(e) => setStepData({ ...stepData, order: Number(e.target.value) })}
              required
            />
          </Form.Group>
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onHide}>Close</Button>
        <Button variant="primary" onClick={handleSave}>Save Step</Button>
      </Modal.Footer>
    </Modal>
  );
};

export default HelpStepForm;
