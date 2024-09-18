import { useState, useCallback, useEffect } from 'react';

const useToasts = () => {
  const [toasts, setToasts] = useState([]);
  const [toastTimeout] = useState(5000); // Default duration for toast visibility

  const showToast = useCallback((variant, message, heading) => {
    const newToast = {
      id: Date.now(),
      variant,
      message,
      heading,
      time: new Date(),
    };

    // Use a Set to track existing messages for efficient duplicate checking
    const existingMessages = new Set(toasts.map(toast => toast.message));
    if (!existingMessages.has(message)) {
      setToasts(prevToasts => [...prevToasts, newToast]);
    }
  }, [toasts]);

  const removeToast = useCallback((id) => {
    setToasts(prevToasts => prevToasts.filter(toast => toast.id !== id));
  }, []);

  // Auto-remove toasts after the specified duration
  useEffect(() => {
    if (toasts.length > 0) {
      const timer = setTimeout(() => {
        setToasts(prevToasts => prevToasts.slice(1)); // Remove the oldest toast
      }, toastTimeout);

      return () => clearTimeout(timer); // Clear the timeout on cleanup
    }
  }, [toasts, toastTimeout]);

  return { toasts, showToast, removeToast };
};

export default useToasts;
