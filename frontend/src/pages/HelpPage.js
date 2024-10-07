import React, { useState, useCallback } from 'react';
import api from '../services/api';
import { Table, Button, Modal } from 'react-bootstrap';
import HelpTourForm from '../components/HelpTourForm';
import HelpTourStepForm from '../components/HelpTourStepForm'; // New component for creating steps
import Loading from '../components/Loading';

const HelpPage = ({ showToast }) => {
  const [showTourForm, setShowTourForm] = useState(false);
  const [showStepForm, setShowStepForm] = useState(false);
  const [selectedTour, setSelectedTour] = useState(null);
  const [tours, setTours] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Function to fetch tours
  const fetchTours = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/help/tours');
      setTours(response.data);
    } catch (error) {
      console.error('Error fetching tours:', error);
      setError('Failed to fetch tours.');
      showToast('danger', 'Failed to fetch tours.', 'Error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  // Fetch tours on component mount
  React.useEffect(() => {
    fetchTours();
  }, [fetchTours]);

  // Open the modal to add a new tour or edit an existing one
  const openTourForm = (tour = null) => {
    setSelectedTour(tour);
    setShowTourForm(true);
  };

  // Open the modal to create a new tour step
  const openStepForm = () => {
    setShowStepForm(true);
  };

  return (
    <div className="container mt-5" role="main">
      <h1 className="text-center mb-4" aria-live="polite">Help Center</h1>
      <div className="d-flex justify-content-end mb-3">
        <Button variant="primary" onClick={openStepForm}>
          Add Step
        </Button>
        <Button variant="secondary" className="ms-2" onClick={() => openTourForm()}>
          Add Tour
        </Button>
      </div>
      {loading ? (
        <Loading />
      ) : error ? (
        <p className="text-danger" role="alert">{error}</p>
      ) : (
        <Table striped bordered hover responsive>
          <thead>
            <tr>
              <th>ID</th>
              <th>User ID</th>
              <th>Status</th>
              <th>Completed At</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {tours.map((tour) => (
              <tr key={tour.id}>
                <td>{tour.id}</td>
                <td>{tour.user_id}</td>
                <td>{tour.completed ? 'Completed' : 'In Progress'}</td>
                <td>{tour.completed_at || 'N/A'}</td>
                <td>
                  <Button variant="info" onClick={() => openTourForm(tour)}>Edit</Button>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      {/* Modal for adding/editing a tour */}
      {showTourForm && (
        <Modal show={showTourForm} onHide={() => setShowTourForm(false)} centered>
          <Modal.Header closeButton>
            <Modal.Title>{selectedTour ? 'Edit Tour' : 'Add New Tour'}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <HelpTourForm
              tour={selectedTour}
              fetchTours={fetchTours}
              onHide={() => setShowTourForm(false)}
              showToast={showToast}
            />
          </Modal.Body>
        </Modal>
      )}

      {/* Modal for adding a new step */}
      {showStepForm && (
        <Modal show={showStepForm} onHide={() => setShowStepForm(false)} centered>
          <Modal.Header closeButton>
            <Modal.Title>Add New Step</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <HelpTourStepForm
              fetchTours={fetchTours}
              onHide={() => setShowStepForm(false)}
              showToast={showToast}
            />
          </Modal.Body>
        </Modal>
      )}
    </div>
  );
};

export default HelpPage;
