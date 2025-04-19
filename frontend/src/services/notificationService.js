class NotificationService {
  static showSuccess(toastContext, message, title = 'Success') {
    const { showToast } = toastContext;
    showToast('success', message, title);
  }

  static showError(toastContext, message, title = 'Error') {
    const { showToast } = toastContext;
    showToast('danger', message, title);
  }

  static showWarning(toastContext, message, title = 'Warning') {
    const { showToast } = toastContext;
    showToast('warning', message, title);
  }

  static showInfo(toastContext, message, title = 'Info') {
    const { showToast } = toastContext;
    showToast('info', message, title);
  }

  static handleApiError(toastContext, error, defaultMessage = 'An error occurred') {
    const { showToast } = toastContext;

    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      const message = error.response.data?.message || defaultMessage;
      showToast('danger', message, 'Error');
    } else if (error.request) {
      // The request was made but no response was received
      showToast('danger', 'No response from server. Please try again later.', 'Error');
    } else {
      // Something happened in setting up the request that triggered an Error
      showToast('danger', error.message || defaultMessage, 'Error');
    }
  }

  static handleTourError(toastContext, error) {
    this.handleApiError(toastContext, error, 'Failed to update tour status');
  }

  static handleStepError(toastContext, error) {
    this.handleApiError(toastContext, error, 'Failed to update step status');
  }
}

export default NotificationService;
