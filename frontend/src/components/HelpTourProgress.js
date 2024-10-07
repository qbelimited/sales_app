import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import Loading from '../components/Loading';
import { Table, Button } from 'react-bootstrap';
import HelpTourDetails from './HelpTourDetails';

const HelpTourProgress = ({ showToast }) => {
  const [tours, setTours] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTour, setSelectedTour] = useState(null);

  const fetchTours = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/help/tours');
      setTours(response.data);
    } catch (error) {
      console.error('Error fetching tours:', error);
      setError('Failed to fetch user tours.');
      showToast('danger', 'Failed to fetch user tours.', 'Error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchTours();
  }, [fetchTours]);

  return (
    <div className="help-tour-progress mt-5">
      <h2>User Tour Progress</h2>
      {loading ? (
        <Loading />
      ) : error ? (
        <p className="text-danger" role="alert">{error}</p>
      ) : (
        <Table striped bordered hover responsive>
          <thead>
            <tr>
              <th>User ID</th>
              <th>Status</th>
              <th>Completed At</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {tours.map((tour) => (
              <tr key={tour.id}>
                <td>{tour.user_id}</td>
                <td>{tour.completed ? 'Completed' : 'In Progress'}</td>
                <td>{tour.completed_at || 'N/A'}</td>
                <td>
                  <Button
                    variant="info"
                    onClick={() => setSelectedTour(tour)}
                  >
                    View Details
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
      {selectedTour && (
        <HelpTourDetails
          userId={selectedTour.user_id}
          onClose={() => setSelectedTour(null)}
          showToast={showToast}
        />
      )}
    </div>
  );
};

export default HelpTourProgress;
