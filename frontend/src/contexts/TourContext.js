// TourContext.js
import React, { createContext, useContext, useState, useEffect } from 'react';

const TourContext = createContext();

export const useTour = () => {
  return useContext(TourContext);
};

export const TourProvider = ({ children }) => {
  const [run, setRun] = useState(false);      // Track if the tour is running
  const [steps, setSteps] = useState([]);     // Store the steps for the current tour
  const [userId, setUserId] = useState(null); // Store the current user's ID

  useEffect(() => {
    // Fetch user data from local storage
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      const user = JSON.parse(storedUser); // Parse the user data from JSON
      setUserId(user.id); // Set the user ID from the user object
    }
  }, []); // Runs once when the component mounts

  const startTour = () => setRun(true);       // Start the tour
  const stopTour = () => setRun(false);       // Stop the tour
  const setTourSteps = (newSteps) => setSteps(newSteps); // Set the steps for the tour

  const updateUserId = (id) => {
    setUserId(id);
    // Update the user ID in local storage if necessary
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      const user = JSON.parse(storedUser);
      user.id = id; // Update user ID
      localStorage.setItem('user', JSON.stringify(user)); // Save updated user back to local storage
    }
  };

  return (
    <TourContext.Provider value={{ run, startTour, stopTour, steps, setTourSteps, userId, updateUserId }}>
      {children}
    </TourContext.Provider>
  );
};
