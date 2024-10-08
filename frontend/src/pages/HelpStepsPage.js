import React, { useState, useCallback, useEffect } from 'react';
import api from '../services/api';
import { Table, Button, Modal, Pagination, Spinner } from 'react-bootstrap';
import { FaPlus, FaEdit, FaTrash, FaArrowLeft } from 'react-icons/fa'; // Import Font Awesome icons
import HelpStepForm from '../components/HelpStepForm';
import Loading from '../components/Loading';
import PropTypes from 'prop-types';
import { useNavigate } from 'react-router-dom';

const HelpStepsPage = ({ showToast }) => {
  const [showStepForm, setShowStepForm] = useState(false);
  const [selectedStep, setSelectedStep] = useState(null);
  const [steps, setSteps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Modal for delete confirmation
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [stepToDelete, setStepToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const stepsPerPage = 10;

  const navigate = useNavigate();

  const fetchSteps = useCallback(async () => {
    let isMounted = true; // Flag to check if the component is mounted
    setLoading(true);
    setError(null);

    try {
      const response = await api.get('/help/steps');
      if (isMounted) setSteps(response.data);
    } catch (error) {
      console.error('Error fetching steps:', error);
      if (isMounted) {
        setError('Failed to fetch steps.');
        showToast('danger', 'Failed to fetch steps.', 'Error');
      }
    } finally {
      if (isMounted) setLoading(false);
    }

    return () => {
      isMounted = false; // Cleanup function to prevent state updates on unmounted component
    };
  }, [showToast]);

  useEffect(() => {
    fetchSteps();
  }, [fetchSteps]);

  const openStepForm = (step = null) => {
    setSelectedStep(step);
    setShowStepForm(true);
  };

  const handleDeleteStep = (stepId) => {
    setStepToDelete(stepId);
    setShowDeleteModal(true);
  };

  const confirmDeleteStep = async () => {
    setIsDeleting(true);
    try {
      await api.delete(`/help/steps/${stepToDelete}`);
      showToast('success', 'Step deleted successfully.', 'Success');
      fetchSteps(); // Refresh the list
    } catch (error) {
      console.error('Error deleting step:', error);
      showToast('danger', 'Failed to delete step.', 'Error');
    } finally {
      setShowDeleteModal(false);
      setStepToDelete(null); // Reset the stepToDelete
      setIsDeleting(false);
    }
  };

  // Pagination logic
  const indexOfLastStep = currentPage * stepsPerPage;
  const indexOfFirstStep = indexOfLastStep - stepsPerPage;
  const currentSteps = steps.slice(indexOfFirstStep, indexOfLastStep);

  const paginate = (pageNumber) => setCurrentPage(pageNumber);

  // Reset current page when the steps data changes
  useEffect(() => {
    setCurrentPage(1);
  }, [steps]);

  if (loading) return <Loading />;

  return (
    <div className="container mt-5" role="main">
      <Button variant="secondary" onClick={() => navigate(-1)} className="mb-4">
        <FaArrowLeft className="me-1" /> Back
      </Button> {/* Back button */}
      <h1 className="text-center mb-4">Help Steps</h1>
      <div className="d-flex justify-content-end mb-3">
        <Button variant="secondary" onClick={openStepForm}>
          <FaPlus className="me-1" /> Add Step
        </Button>
      </div>
      {error && <p className="text-danger" role="alert">{error}</p>}
      {steps.length === 0 ? (
        <div className="text-center">
          <p>No data available.</p>
          <Button variant="secondary" onClick={openStepForm}>
            <FaPlus className="me-1" /> Add a Step
          </Button>
        </div>
      ) : (
        <>
          <Table striped bordered hover responsive>
            <thead>
              <tr>
                <th>ID</th>
                <th>Page Name</th>
                <th>Target</th>
                <th>Step Content</th>
                <th>Order</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {currentSteps.map((step) => (
                <tr key={step.id}>
                  <td>{step.id}</td>
                  <td>{step.page_name}</td>
                  <td>{step.target}</td>
                  <td>{step.content}</td>
                  <td>{step.order}</td>
                  <td>
                    <Button
                      variant="info"
                      onClick={() => openStepForm(step)}
                      aria-label={`Edit step ${step.id}`}
                    >
                      <FaEdit className="me-1" /> Edit
                    </Button>
                    <Button
                      variant="danger"
                      className="ms-2"
                      onClick={() => handleDeleteStep(step.id)}
                      aria-label={`Delete step ${step.id}`}
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
            {Array.from({ length: Math.ceil(steps.length / stepsPerPage) }, (_, index) => (
              <Pagination.Item
                key={index + 1}
                active={index + 1 === currentPage}
                onClick={() => paginate(index + 1)}
              >
                {index + 1}
              </Pagination.Item>
            ))}
            <Pagination.Next
              onClick={() => setCurrentPage((prev) => Math.min(prev + 1, Math.ceil(steps.length / stepsPerPage)))}
              disabled={currentPage === Math.ceil(steps.length / stepsPerPage)}
            />
          </Pagination>
        </>
      )}

      {/* Modal for adding/editing a step */}
      <Modal show={showStepForm} onHide={() => setShowStepForm(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>{selectedStep ? 'Edit Step' : 'Add New Step'}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <HelpStepForm
            step={selectedStep}
            fetchSteps={fetchSteps}
            onHide={() => setShowStepForm(false)}
            showToast={showToast}
          />
        </Modal.Body>
      </Modal>

      {/* Modal for delete confirmation */}
      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Deletion</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>Are you sure you want to delete this step?</p>
          {isDeleting && <Spinner animation="border" variant="danger" />}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={confirmDeleteStep} disabled={isDeleting}>
            {isDeleting ? 'Deleting...' : 'Delete'}
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

HelpStepsPage.propTypes = {
  showToast: PropTypes.func.isRequired,
};

export default HelpStepsPage;
