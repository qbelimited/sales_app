import { useToastContext } from '../contexts/ToastContext';

export const useNotification = () => {
  const { showToast } = useToastContext();

  const showSuccess = (message, title = 'Success') => {
    showToast('success', message, title);
  };

  const showError = (message, title = 'Error') => {
    showToast('danger', message, title);
  };

  const showWarning = (message, title = 'Warning') => {
    showToast('warning', message, title);
  };

  const showInfo = (message, title = 'Info') => {
    showToast('info', message, title);
  };

  const handleApiError = (error, defaultMessage = 'An error occurred') => {
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      const message = error.response.data?.message || defaultMessage;
      showError(message);
    } else if (error.request) {
      // The request was made but no response was received
      showError('No response from server. Please try again later.');
    } else {
      // Something happened in setting up the request that triggered an Error
      showError(error.message || defaultMessage);
    }
  };

  const handleTourError = (error) => {
    handleApiError(error, 'Failed to update tour status');
  };

  const handleStepError = (error) => {
    handleApiError(error, 'Failed to update step status');
  };

  return {
    showSuccess,
    showError,
    showWarning,
    showInfo,
    handleApiError,
    handleTourError,
    handleStepError
  };
};
