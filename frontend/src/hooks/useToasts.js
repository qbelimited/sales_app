// hooks/useToasts.js
import { useState, useCallback } from 'react';

const useToasts = () => {
  const [toasts, setToasts] = useState([]);

  const showToast = useCallback((variant, message, heading) => {
    const newToast = {
      id: Date.now(),
      variant,
      message,
      heading,
      time: new Date(),  // Include time to display how long ago the toast was created
    };
    const isDuplicate = toasts.some((toast) => toast.message === message && toast.variant === variant);
    if (!isDuplicate) setToasts((prevToasts) => [...prevToasts, newToast]);
  }, [toasts]);

  const removeToast = useCallback((id) => {
    setToasts((prevToasts) => prevToasts.filter((t) => t.id !== id));
  }, []);

  return { toasts, showToast, removeToast };
};

export default useToasts;
