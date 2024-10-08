import React, { useEffect, useState } from 'react';
import Joyride from 'react-joyride';
import { useTour } from '../contexts/TourContext'; // Adjust the import based on your file structure
import api from '../services/api'; // Ensure axios is installed
import { useLocation } from 'react-router-dom'; // To get the current page name

const HelpTour = () => {
  const { run, stopTour, userId, setTourSteps } = useTour();
  const [steps, setSteps] = useState([]);
  const [loading, setLoading] = useState(true);
  const location = useLocation();

  useEffect(() => {
    const fetchTourStatusAndSteps = async () => {
      setLoading(true);
      if (!userId) {
        setLoading(false);
        return;
      }

      const pageName = location.pathname.replace('/', '') || 'home';

      try {
        const { data: tour } = await api.get(`/help/tours?page_name=${pageName}`);

        if (tour && !tour.completed && tour.steps?.length > 0) {
          setSteps(tour.steps);
          setTourSteps(tour.steps);
          run(); // Start the tour
        }
      } catch (error) {
        console.error("Error fetching help tour status:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchTourStatusAndSteps();
  }, [userId, setTourSteps, location, run]);

  const handleTourEnd = async (data) => {
    if (data.status === 'finished' || data.status === 'skipped') {
      stopTour();
      try {
        await api.put(`/help/tours/${data.tourId}`, { completed: true });
      } catch (error) {
        console.error("Error marking tour as completed:", error);
      }
    }
  };

  if (loading) {
    return <div>Loading tour...</div>;
  }

  return (
    <Joyride
      steps={steps}
      run={run}
      continuous
      showSkipButton
      showProgress
      styles={{
        options: {
          zIndex: 10000,
        },
      }}
      callback={handleTourEnd}
    />
  );
};

export default HelpTour;
