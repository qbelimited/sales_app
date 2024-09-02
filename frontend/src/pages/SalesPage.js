import React from 'react';
import SalesForm from '../components/SalesForm';

function SalesPage() {
  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-md-8">
          <h1 className="text-center mb-4">Sales Records</h1>
          <SalesForm />
        </div>
      </div>
    </div>
  );
}

export default SalesPage;
