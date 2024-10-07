import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import { Modal, Button, Form } from 'react-bootstrap';
import Loading from './Loading';

const HelpTourManager = ({ showToast }) => {
  const [steps, setSteps] = useState([]);
  const [selectedStep, setSelectedStep] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [newStep, setNewStep] = useState({ page_name: '', target: '', content: '', order: 0 });

  const fetchSteps = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get('/help/steps');
      setSteps(response.data);
    } catch (error) {
      console.error('Error fetching steps:', error);
      showToast('danger', 'Failed to fetch help steps.', 'Error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchSteps();
  }, [fetchSteps]);

  const handleAddStep = async () => {
    try {
      await api.post('/help/steps', newStep);
      showToast('success', 'Step added successfully.', 'Success');
      fetchSteps();
    } catch (error) {
      console.error('Error adding step:', error);
      showToast('danger', 'Failed to add step.', 'Error');
    }
  };

  const handleUpdateStep = async () => {
    try {
      await api.put(`/help/steps/${selectedStep.id}`, selectedStep);
      showToast('success', 'Step updated successfully.', 'Success');
      fetchSteps();
    } catch (error) {
      console.error('Error updating step:', error);
      showToast('danger', 'Failed to update step.', 'Error');
    } finally {
      setShowEditModal(false);
    }
  };

  const handleDeleteStep = async (stepId) => {
    try {
      await api.delete(`/help/steps/${stepId}`);
      showToast('success', 'Step deleted successfully.', 'Success');
      fetchSteps();
    } catch (error) {
      console.error('Error deleting step:', error);
      showToast('danger', 'Failed to delete the step.', 'Error');
    } finally {
      setShowDeleteModal(false);
    }
  };

  return (
    <div className="help-tour-manager">
      <h2>Manage Help Tour Steps</h2>
      {loading ? (
        <Loading />
      ) : (
        <ul>
          {steps.map((step) => (
            <li key={step.id}>
              {step.content} - {step.target}
              <Button variant="primary" onClick={() => {
                setSelectedStep(step);
                setShowEditModal(true);
              }}>
                Edit
              </Button>
              <Button variant="danger" onClick={() => {
                setSelectedStep(step);
                setShowDeleteModal(true);
              }}>
                Delete
              </Button>
            </li>
          ))}
        </ul>
      )}

      <Form onSubmit={(e) => {
        e.preventDefault();
        handleAddStep();
      }}>
        <h3>Add New Step</h3>
        <Form.Group>
          <Form.Label>Page Name</Form.Label>
          <Form.Control
            type="text"
            value={newStep.page_name}
            onChange={(e) => setNewStep({ ...newStep, page_name: e.target.value })}
          />
        </Form.Group>
        <Form.Group>
          <Form.Label>Target</Form.Label>
          <Form.Control
            type="text"
            value={newStep.target}
            onChange={(e) => setNewStep({ ...newStep, target: e.target.value })}
          />
        </Form.Group>
        <Form.Group>
          <Form.Label>Content</Form.Label>
          <Form.Control
            as="textarea"
            rows={3}
            value={newStep.content}
            onChange={(e) => setNewStep({ ...newStep, content: e.target.value })}
          />
        </Form.Group>
        <Form.Group>
          <Form.Label>Order</Form.Label>
          <Form.Control
            type="number"
            value={newStep.order}
            onChange={(e) => setNewStep({ ...newStep, order: Number(e.target.value) })}
          />
        </Form.Group>
        <Button type="submit" variant="success">Add Step</Button>
      </Form>

      {/* Delete Confirmation Modal */}
      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Delete</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Are you sure you want to delete this step?
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>Cancel</Button>
          <Button variant="danger" onClick={() => handleDeleteStep(selectedStep.id)}>Delete</Button>
        </Modal.Footer>
      </Modal>

      {/* Edit Step Modal */}
      {showEditModal && (
        <Modal show={showEditModal} onHide={() => setShowEditModal(false)} centered>
          <Modal.Header closeButton>
            <Modal.Title>Edit Step</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Form>
              <Form.Group>
                <Form.Label>Page Name</Form.Label>
                <Form.Control
                  type="text"
                  value={selectedStep.page_name}
                  onChange={(e) => setSelectedStep({ ...selectedStep, page_name: e.target.value })}
                />
              </Form.Group>
              <Form.Group>
                <Form.Label>Target</Form.Label>
                <Form.Control
                  type="text"
                  value={selectedStep.target}
                  onChange={(e) => setSelectedStep({ ...selectedStep, target: e.target.value })}
                />
              </Form.Group>
              <Form.Group>
                <Form.Label>Content</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={3}
                  value={selectedStep.content}
                  onChange={(e) => setSelectedStep({ ...selectedStep, content: e.target.value })}
                />
              </Form.Group>
              <Form.Group>
                <Form.Label>Order</Form.Label>
                <Form.Control
                  type="number"
                  value={selectedStep.order}
                  onChange={(e) => setSelectedStep({ ...selectedStep, order: Number(e.target.value) })}
                />
              </Form.Group>
            </Form>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowEditModal(false)}>Cancel</Button>
            <Button variant="primary" onClick={handleUpdateStep}>Save Changes</Button>
          </Modal.Footer>
        </Modal>
      )}
    </div>
  );
};

export default HelpTourManager;
