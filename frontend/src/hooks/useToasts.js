import { useState, useCallback, useEffect } from 'react';

const useToasts = () => {
  const [toasts, setToasts] = useState([]);
  const toastTimeout = 5000; // Default duration for toast visibility

  // Show a new toast message
  const showToast = useCallback((variant, message, heading) => {
    const newToast = {
      id: Date.now(),
      variant,
      message,
      heading,
      time: new Date(),
    };

    // Check for existing messages to prevent duplicates
    const existingMessages = new Set(toasts.map(toast => toast.message));
    if (!existingMessages.has(message)) {
      setToasts(prevToasts => [...prevToasts, newToast]);
    }
  }, [toasts]);

  // Remove a toast by ID
  const removeToast = useCallback((id) => {
    setToasts(prevToasts => prevToasts.filter(toast => toast.id !== id));
  }, []);

  // Auto-remove toasts after the specified duration
  useEffect(() => {
    if (toasts.length > 0) {
      const timer = setTimeout(() => {
        removeToast(toasts[0].id); // Remove the oldest toast
      }, toastTimeout);

      return () => clearTimeout(timer); // Clear the timeout on cleanup
    }
  }, [toasts, toastTimeout, removeToast]); // Include removeToast in dependencies

  return { toasts, showToast, removeToast };
};

export default useToasts;
