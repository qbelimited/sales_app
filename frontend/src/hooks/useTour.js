import { useState, useEffect, useCallback } from 'react';
import TourService from '../services/tourService';
import { useToastContext } from '../contexts/ToastContext';

export const useTour = (userId) => {
  const [tour, setTour] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { showToast } = useToastContext();

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
      showToast('danger', 'Failed to fetch tour status', 'Error');
    } finally {
      setLoading(false);
    }
  }, [userId, showToast]);

  const updateStepStatus = useCallback(async (stepId, status) => {
    if (!tour) return;

    try {
      if (status === 'completed') {
        await TourService.markStepCompleted(tour.id, stepId);
      } else if (status === 'skipped') {
        await TourService.markStepSkipped(tour.id, stepId);
      }
      fetchTour(); // Refresh tour data
    } catch (error) {
      console.error('Error updating step status:', error);
      showToast('danger', 'Failed to update step status', 'Error');
    }
  }, [tour, fetchTour, showToast]);

  const resetTour = useCallback(async () => {
    if (!tour) return;

    try {
      await TourService.resetTour(tour.id);
      fetchTour(); // Refresh tour data
      showToast('success', 'Tour reset successfully', 'Success');
    } catch (error) {
      console.error('Error resetting tour:', error);
      showToast('danger', 'Failed to reset tour', 'Error');
    }
  }, [tour, fetchTour, showToast]);

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
