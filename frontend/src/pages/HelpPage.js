import React, { useState, useCallback, useEffect } from 'react';
import api from '../services/api';
import { Table, Button, Modal, Pagination, Spinner } from 'react-bootstrap';
import { FaPlus, FaEdit, FaTrash, FaQuestionCircle, FaTasks } from 'react-icons/fa'; // Import Font Awesome icons
import HelpTourForm from '../components/HelpTourForm';
import Loading from '../components/Loading';
import PropTypes from 'prop-types';
import { useNavigate } from 'react-router-dom'; // Import useNavigate

const HelpPage = ({ showToast }) => {
  const [showTourForm, setShowTourForm] = useState(false);
  const [selectedTour, setSelectedTour] = useState(null);
  const [tours, setTours] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Modal for delete confirmation
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [tourToDelete, setTourToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const toursPerPage = 10;

  const navigate = useNavigate(); // Initialize navigate

  const fetchTours = useCallback(async () => {
    let isMounted = true; // Flag to check if the component is mounted
    setLoading(true);
    setError(null);

    try {
      const response = await api.get('/help/tours');
      if (isMounted) setTours(response.data);
    } catch (error) {
      console.error('Error fetching tours:', error);
      if (isMounted) {
        if (error.response && error.response.status === 404) {
          setError('No tours found. You can add a new tour.');
        } else {
          setError('Failed to fetch tours.');
          showToast('danger', 'Failed to fetch tours.', 'Error');
        }
      }
    } finally {
      if (isMounted) setLoading(false);
    }

    return () => {
      isMounted = false; // Cleanup function to prevent state updates on unmounted component
    };
  }, [showToast]);

  useEffect(() => {
    fetchTours();
  }, [fetchTours]);

  const openTourForm = (tour = null) => {
    setSelectedTour(tour);
    setShowTourForm(true);
  };

  const handleDeleteTour = (tourId) => {
    setTourToDelete(tourId);
    setShowDeleteModal(true);
  };

  const confirmDeleteTour = async () => {
    setIsDeleting(true);
    try {
      await api.delete(`/help/tours/${tourToDelete}`);
      showToast('success', 'Tour deleted successfully.', 'Success');
      fetchTours(); // Refresh the list
    } catch (error) {
      console.error('Error deleting tour:', error);
      showToast('danger', 'Failed to delete tour.', 'Error');
    } finally {
      setShowDeleteModal(false);
      setTourToDelete(null); // Reset the tourToDelete
      setIsDeleting(false);
    }
  };

  const handleAddOrEditTour = async (tourData) => {
    try {
      if (selectedTour) {
        // Edit existing tour
        await api.put(`/help/tours/${selectedTour.id}`, {
          ...tourData,
          completed: selectedTour.completed,
          completed_at: selectedTour.completed_at,
        });
        showToast('success', 'Tour updated successfully.', 'Success');
      } else {
        // Add new tour
        await api.post('/help/tours', {
          user_id: tourData.user_id, // Ensure to pass user ID if needed
          completed: false,
          completed_at: null,
          steps: tourData.steps, // Assuming this contains the steps structure
        });
        showToast('success', 'Tour added successfully.', 'Success');
      }
      fetchTours(); // Refresh the list after add or edit
      setShowTourForm(false); // Close the form
      setSelectedTour(null); // Reset selected tour
    } catch (error) {
      console.error('Error saving tour:', error);
      showToast('danger', 'Failed to save tour.', 'Error');
    }
  };

  // Pagination logic
  const indexOfLastTour = currentPage * toursPerPage;
  const indexOfFirstTour = indexOfLastTour - toursPerPage;
  const currentTours = tours.slice(indexOfFirstTour, indexOfLastTour);

  const paginate = (pageNumber) => setCurrentPage(pageNumber);

  // Reset current page when the tours data changes
  useEffect(() => {
    setCurrentPage(1);
  }, [tours]);

  if (loading) return <Loading />;

  return (
    <div className="container mt-5" role="main">
      <h1 className="text-center mb-4" aria-live="polite">
        Help Center <FaQuestionCircle />
      </h1>
      <div className="d-flex justify-content-end mb-3">
        <Button variant="secondary" onClick={() => openTourForm()}> {/* Clear selectedTour for adding */}
          <FaPlus className="me-1" /> Add Tour
        </Button>
        <Button
          variant="primary"
          onClick={() => navigate('/help/steps')} // Navigate to Help Steps page
        >
          <FaTasks className="me-1" /> Manage Tour Steps
        </Button>
      </div>
      {error && <p className="text-danger" role="alert">{error}</p>}
      {tours.length === 0 ? (
        <div className="text-center">
          <p>No data available.</p>
          <Button variant="secondary" onClick={() => openTourForm()}> {/* Clear selectedTour for adding */}
            <FaPlus className="me-1" /> Add a Tour
          </Button>
        </div>
      ) : (
        <>
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
              {currentTours.map((tour) => (
                <tr key={tour.id}>
                  <td>{tour.id}</td>
                  <td>{tour.user_id}</td>
                  <td>{tour.completed ? 'Completed' : 'In Progress'}</td>
                  <td>{tour.completed_at || 'N/A'}</td>
                  <td>
                    <Button
                      variant="info"
                      onClick={() => openTourForm(tour)} // Pass the selected tour for editing
                      aria-label={`Edit tour ${tour.id}`}
                    >
                      <FaEdit className="me-1" /> Edit
                    </Button>
                    <Button
                      variant="danger"
                      className="ms-2"
                      onClick={() => handleDeleteTour(tour.id)}
                      aria-label={`Delete tour ${tour.id}`}
                    >
                      <FaTrash className="me-1" /> Delete
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>

          {/* Pagination */}
          <Pagination>
            <Pagination.Prev
              onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
            />
            {Array.from({ length: Math.ceil(tours.length / toursPerPage) }, (_, index) => (
              <Pagination.Item
                key={index + 1}
                active={index + 1 === currentPage}
                onClick={() => paginate(index + 1)}
              >
                {index + 1}
              </Pagination.Item>
            ))}
            <Pagination.Next
              onClick={() => setCurrentPage((prev) => Math.min(prev + 1, Math.ceil(tours.length / toursPerPage)))}
              disabled={currentPage === Math.ceil(tours.length / toursPerPage)}
            />
          </Pagination>
        </>
      )}

      {/* Modal for adding/editing a tour */}
      <Modal show={showTourForm} onHide={() => setShowTourForm(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>{selectedTour ? 'Edit Tour' : 'Add New Tour'}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <HelpTourForm
            tour={selectedTour} // Pass selected tour for editing
            fetchTours={fetchTours}
            onHide={() => setShowTourForm(false)}
            showToast={showToast}
            onSubmit={handleAddOrEditTour} // Pass the handler to the form
          />
        </Modal.Body>
      </Modal>

      {/* Modal for delete confirmation */}
      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Deletion</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>Are you sure you want to delete this tour?</p>
          {isDeleting && <Spinner animation="border" variant="danger" />}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={confirmDeleteTour} disabled={isDeleting}>
            {isDeleting ? 'Deleting...' : 'Delete'}
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

HelpPage.propTypes = {
  showToast: PropTypes.func.isRequired,
};

export default HelpPage;
