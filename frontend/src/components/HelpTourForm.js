import React, { useState } from 'react';
import { Form, Button } from 'react-bootstrap';
import api from '../services/api';

const HelpTourForm = ({ tour, fetchTours, onHide, showToast }) => {
  const [tourData, setTourData] = useState(tour || {
    user_id: '',
    completed: false,
  });

  const handleSave = async () => {
    try {
      if (tourData.id) {
        await api.put(`/help/tours/${tourData.id}`, tourData);
        showToast('success', 'Tour updated successfully.', 'Success');
      } else {
        await api.post('/help/tours', tourData);
        showToast('success', 'Tour added successfully.', 'Success');
      }
      fetchTours();
      onHide();
    } catch (error) {
      console.error('Error saving tour:', error);
      showToast('danger', 'Failed to save tour.', 'Error');
    }
  };

  return (
    <Form>
      <Form.Group>
        <Form.Label>User ID</Form.Label>
        <Form.Control
          type="text"
          value={tourData.user_id}
          onChange={(e) => setTourData({ ...tourData, user_id: e.target.value })}
          disabled={!!tourData.id} // Disable editing user_id when updating
        />
      </Form.Group>
      <Form.Group>
        <Form.Label>Status</Form.Label>
        <Form.Check
          type="checkbox"
          label="Completed"
          checked={tourData.completed}
          onChange={(e) => setTourData({ ...tourData, completed: e.target.checked })}
        />
      </Form.Group>
      <Button variant="primary" onClick={handleSave}>
        {tourData.id ? 'Update' : 'Create'}
      </Button>
    </Form>
  );
};

export default HelpTourForm;
