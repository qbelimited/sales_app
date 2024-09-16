// HelpTour.js
import React, { useState } from 'react';
import Joyride from 'react-joyride';

const HelpTour = () => {
  const [run, setRun] = useState(true);

  const steps = [
    {
      target: '.navbar',
      content: 'This is the navigation bar where you can find the menu options.',
    },
    {
      target: '.sidebar',
      content: 'Here is the sidebar with different sections of the app.',
    },
    {
      target: '.sales-table',
      content: 'This table displays the sales data.',
    },
  ];

  return (
    <Joyride
      steps={steps}
      run={run}
      continuous
      showSkipButton
      showProgress
      styles={{
        options: {
          zIndex: 10000,
        },
      }}
      callback={(data) => {
        if (data.status === 'finished' || data.status === 'skipped') {
          setRun(false);
        }
      }}
    />
  );
};

export default HelpTour;
