import React, { useState } from 'react';
import { Form, Button } from 'react-bootstrap';
import api from '../services/api';

const HelpTourStepForm = ({ fetchTours, onHide, showToast }) => {
  const [stepData, setStepData] = useState({
    page_name: '',
    target: '',
    content: '',
    order: 0,
  });

  const handleSave = async () => {
    try {
      await api.post('/help/steps', stepData);
      showToast('success', 'Step created successfully.', 'Success');
      fetchTours(); // Refresh the list of tours
      onHide(); // Close the modal
    } catch (error) {
      console.error('Error creating step:', error);
      showToast('danger', 'Failed to create step.', 'Error');
    }
  };

  return (
    <Form>
      <Form.Group>
        <Form.Label>Page Name</Form.Label>
        <Form.Control
          type="text"
          value={stepData.page_name}
          onChange={(e) => setStepData({ ...stepData, page_name: e.target.value })}
          placeholder="Enter page name"
        />
      </Form.Group>
      <Form.Group>
        <Form.Label>Target</Form.Label>
        <Form.Control
          type="text"
          value={stepData.target}
          onChange={(e) => setStepData({ ...stepData, target: e.target.value })}
          placeholder="Enter target element"
        />
      </Form.Group>
      <Form.Group>
        <Form.Label>Content</Form.Label>
        <Form.Control
          as="textarea"
          rows={3}
          value={stepData.content}
          onChange={(e) => setStepData({ ...stepData, content: e.target.value })}
          placeholder="Enter step content"
        />
      </Form.Group>
      <Form.Group>
        <Form.Label>Order</Form.Label>
        <Form.Control
          type="number"
          value={stepData.order}
          onChange={(e) => setStepData({ ...stepData, order: parseInt(e.target.value, 10) })}
          placeholder="Enter display order"
        />
      </Form.Group>
      <Button variant="primary" onClick={handleSave} className="mt-3">
        Create Step
      </Button>
    </Form>
  );
};

export default HelpTourStepForm;
