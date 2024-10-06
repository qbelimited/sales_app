// hooks/useLocalStorage.js
import { useState, useEffect } from 'react';

// Custom hook for localStorage interaction
export function useLocalStorage(key, initialValue) {
  // State to hold the stored value
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      // Parse the item from local storage or return the initial value
      return item !== null ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error('Failed to retrieve item from local storage:', error);
      return initialValue; // Return initial value on error
    }
  });

  // Function to update the local storage
  const setValue = (value) => {
    try {
      const valueToStore =
        value instanceof Function ? value(storedValue) : value; // Allow function updates
      setStoredValue(valueToStore); // Update state
      window.localStorage.setItem(key, JSON.stringify(valueToStore)); // Update local storage
    } catch (error) {
      console.error('Failed to set item in local storage:', error);
    }
  };

  // Effect to synchronize the local storage when the key changes
  useEffect(() => {
    const item = window.localStorage.getItem(key);
    if (item !== null) {
      setStoredValue(JSON.parse(item));
    }
  }, [key]); // Runs when the key changes

  return [storedValue, setValue]; // Return stored value and update function
}
