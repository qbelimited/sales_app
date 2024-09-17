import { useState, useCallback, useEffect } from 'react';

const useToasts = () => {
  const [toasts, setToasts] = useState([]);

  const showToast = useCallback((variant, message, heading) => {
    const newToast = {
      id: Date.now(),
      variant,
      message,
      heading,
      time: new Date(), // Include time to display how long ago the toast was created
    };
    // Check if a toast with the same message and variant already exists
    const isDuplicate = toasts.some((toast) => toast.message === message && toast.variant === variant);
    if (!isDuplicate) setToasts((prevToasts) => [...prevToasts, newToast]);
  }, [toasts]);

  const removeToast = useCallback((id) => {
    setToasts((prevToasts) => prevToasts.filter((toast) => toast.id !== id));
  }, []);

  // Auto-remove toasts after 5 seconds
  useEffect(() => {
    if (toasts.length > 0) {
      const timer = setTimeout(() => {
        setToasts((prevToasts) => prevToasts.slice(1));
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [toasts]);

  return { toasts, showToast, removeToast };
};

export default useToasts;
