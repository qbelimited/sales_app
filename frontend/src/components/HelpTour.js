import React, { useEffect, useState } from 'react';
import Joyride from 'react-joyride';
import { useTour } from '../hooks/useTour';
import { useLocation } from 'react-router-dom';
import { useNotification } from '../hooks/useNotification';

const HelpTour = () => {
  const { tour, loading, error, updateStepStatus } = useTour();
  const { showSuccess, handleTourError, handleStepError } = useNotification();
  const [steps, setSteps] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const location = useLocation();

  useEffect(() => {
    if (!tour || !tour.steps) return;

    const pageName = location.pathname.replace('/', '') || 'home';
    const activeSteps = tour.steps
      .filter(step => step.page_name === pageName)
      .filter(step => !step.completed && !step.skipped);

    setSteps(activeSteps);
  }, [tour, location.pathname]);

  const handleTourEnd = async (data) => {
    if (data.status === 'finished' || data.status === 'skipped') {
      try {
        await updateStepStatus(data.stepId, 'completed');
        showSuccess('Tour completed successfully!');
      } catch (error) {
        console.error('Error completing tour:', error);
        handleTourError(error);
      }
    }
  };

  const handleStepChange = async (data) => {
    setCurrentStep(data.index);
    if (data.action === 'next' || data.action === 'prev') {
      try {
        await updateStepStatus(data.stepId, 'completed');
      } catch (error) {
        console.error('Error updating step:', error);
        handleStepError(error);
      }
    }
  };

  if (loading) {
    return <div>Loading tour...</div>;
  }

  if (error) {
    return null;
  }

  if (steps.length === 0) {
    return null;
  }

  return (
    <Joyride
      steps={steps}
      run={true}
      continuous={true}
      showProgress={true}
      showSkipButton={true}
      styles={{
        options: {
          primaryColor: '#007bff',
          zIndex: 1000,
        }
      }}
      callback={handleTourEnd}
      stepIndex={currentStep}
      onStepChange={handleStepChange}
    />
  );
};

export default HelpTour;
