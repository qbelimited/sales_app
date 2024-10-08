import React, { useState, useEffect } from 'react';
import { Form, Button, Modal } from 'react-bootstrap';
import api from '../services/api';

const HelpTourForm = ({ tour, fetchTours, onHide, showToast }) => {
  // Initialize state for tour data
  const [tourData, setTourData] = useState({
    user_id: '',
    completed: false,
    steps: [],
  });

  // Effect to populate form with existing tour data when editing
  useEffect(() => {
    if (tour) {
      setTourData({
        user_id: tour.user_id,
        completed: tour.completed,
        steps: tour.steps || [],
      });
    }
  }, [tour]);

  // Handle form submission to save tour data
  const handleSave = async () => {
    if (!tourData.user_id) {
      showToast('danger', 'User ID is required.', 'Error');
      return;
    }

    if (tourData.steps.length === 0 || tourData.steps.some(step => !step.content)) {
      showToast('danger', 'All steps must have content.', 'Error');
      return;
    }

    try {
      if (tour) {
        // Update existing tour
        await api.put(`/help/tours/${tour.id}`, {
          ...tourData,
          completed_at: tour.completed_at,
        });
        showToast('success', 'Tour updated successfully.', 'Success');
      } else {
        // Add new tour
        await api.post('/help/tours', {
          ...tourData,
          completed: false,
          completed_at: null,
        });
        showToast('success', 'Tour added successfully.', 'Success');
      }
      fetchTours(); // Refresh the list after add or edit
      onHide(); // Close the form
    } catch (error) {
      console.error('Error saving tour:', error);
      showToast('danger', 'Failed to save tour.', 'Error');
    }
  };

  const handleAddStep = () => {
    setTourData(prevState => ({
      ...prevState,
      steps: [...prevState.steps, { content: '', order: prevState.steps.length + 1 }],
    }));
  };

  const handleRemoveStep = (index) => {
    setTourData(prevState => {
      const newSteps = prevState.steps.filter((_, i) => i !== index);
      return { ...prevState, steps: newSteps };
    });
  };

  return (
    <Modal show onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title>{tour ? 'Edit Tour' : 'Add Tour'}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Form>
          <Form.Group controlId="formUserId">
            <Form.Label>User ID</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter User ID"
              value={tourData.user_id}
              onChange={(e) => setTourData({ ...tourData, user_id: e.target.value })}
              disabled={!!tour} // Disable editing user_id when updating
              required
            />
          </Form.Group>
          <Form.Group controlId="formCompleted">
            <Form.Label>Status</Form.Label>
            <Form.Check
              type="checkbox"
              label="Completed"
              checked={tourData.completed}
              onChange={(e) => setTourData({ ...tourData, completed: e.target.checked })}
            />
          </Form.Group>
          <Form.Group controlId="formSteps">
            <Form.Label>Steps</Form.Label>
            {tourData.steps.map((step, index) => (
              <div key={index} className="mb-2">
                <Form.Control
                  type="text"
                  placeholder={`Step ${index + 1} Content`}
                  value={step.content}
                  onChange={(e) => {
                    const newSteps = [...tourData.steps];
                    newSteps[index].content = e.target.value;
                    setTourData({ ...tourData, steps: newSteps });
                  }}
                />
                <Button variant="danger" onClick={() => handleRemoveStep(index)} className="mt-1">
                  Remove Step
                </Button>
              </div>
            ))}
            <Button variant="success" onClick={handleAddStep} className="mt-2">
              Add Step
            </Button>
          </Form.Group>
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onHide}>Close</Button>
        <Button variant="primary" onClick={handleSave}>Save Tour</Button>
      </Modal.Footer>
    </Modal>
  );
};

export default HelpTourForm;
