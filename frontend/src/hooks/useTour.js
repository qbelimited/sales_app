import { useState, useEffect, useCallback } from 'react';
import TourService from '../services/tourService';
import { useNotification } from './useNotification';

export const useTour = (userId) => {
  const [tour, setTour] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const {
    showSuccess,
    showInfo,
    handleTourError,
    handleStepError
  } = useNotification();

  const fetchTour = useCallback(async () => {
    if (!userId) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const tourData = await TourService.getTourStatus(userId);
      setTour(tourData);
    } catch (error) {
      console.error('Error fetching tour:', error);
      setError(error);
      handleTourError(error);
    } finally {
      setLoading(false);
    }
  }, [userId, handleTourError]);

  const updateStepStatus = useCallback(async (stepId, status) => {
    if (!tour) return;

    try {
      if (status === 'completed') {
        await TourService.markStepCompleted(tour.id, stepId);
        showSuccess('Step completed successfully');
      } else if (status === 'skipped') {
        await TourService.markStepSkipped(tour.id, stepId);
        showInfo('Step skipped');
      }
      fetchTour(); // Refresh tour data
    } catch (error) {
      console.error('Error updating step status:', error);
      handleStepError(error);
    }
  }, [tour, fetchTour, showSuccess, showInfo, handleStepError]);

  const resetTour = useCallback(async () => {
    if (!tour) return;

    try {
      await TourService.resetTour(tour.id);
      fetchTour(); // Refresh tour data
      showSuccess('Tour reset successfully');
    } catch (error) {
      console.error('Error resetting tour:', error);
      handleTourError(error);
    }
  }, [tour, fetchTour, showSuccess, handleTourError]);

  useEffect(() => {
    fetchTour();
  }, [fetchTour]);

  return {
    tour,
    loading,
    error,
    updateStepStatus,
    resetTour,
    refreshTour: fetchTour
  };
};
