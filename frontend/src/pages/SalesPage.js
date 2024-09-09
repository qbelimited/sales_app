import React, { useState } from 'react';
import SalesForm from '../components/SalesForm';
import SalesTable from '../components/SalesTable';
import { Button, Toast, ToastContainer } from 'react-bootstrap';

function SalesPage() {
  const [salesRecords, setSalesRecords] = useState([]);
  const [showForm, setShowForm] = useState(false); // State to control form visibility
  const [currentSale, setCurrentSale] = useState(null); // State to track the sale being edited
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [toastVariant, setToastVariant] = useState(''); // success or danger for toast feedback

  // Function to handle form submission (for both new sale and edit)
  const handleFormSubmit = (newSale) => {
    if (currentSale) {
      // Update existing sale
      setSalesRecords(
        salesRecords.map((sale) =>
          sale.id === currentSale.id ? { ...sale, ...newSale } : sale
        )
      );
      setToastMessage('Sale record updated successfully!');
    } else {
      // Add new sale
      setSalesRecords([...salesRecords, { id: salesRecords.length + 1, ...newSale }]);
      setToastMessage('Sale record added successfully!');
    }

    setShowForm(false);
    setCurrentSale(null); // Clear the current sale after submission
    setToastVariant('success');
    setShowToast(true);
  };

  // Function to handle editing a sale
  const handleEdit = (sale) => {
    setCurrentSale(sale); // Set the sale to be edited
    setShowForm(true); // Show the form with sale data
  };

  // Function to handle deleting a sale
  const handleDelete = (saleId) => {
    setSalesRecords(salesRecords.filter(sale => sale.id !== saleId));
    setToastMessage('Sale record deleted successfully!');
    setToastVariant('danger');
    setShowToast(true);
  };

  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-md-8">
          <h1 className="text-center mb-4">Sales Records</h1>

          {/* Button to show the SalesForm */}
          {!showForm && (
            <div className="text-center mb-4">
              <Button onClick={() => setShowForm(true)} variant="primary">
                Add New Sale
              </Button>
            </div>
          )}

          {/* Conditionally render SalesForm */}
          {showForm && (
            <SalesForm
              onSubmit={handleFormSubmit}
              initialData={currentSale}
              onCancel={() => setShowForm(false)}
            />
          )}

          {/* Sales Table */}
          <SalesTable
            salesRecords={salesRecords}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />

          {/* Toast Notification */}
          <ToastContainer position="top-end" className="p-3">
            <Toast
              onClose={() => setShowToast(false)}
              show={showToast}
              delay={3000}
              autohide
              bg={toastVariant} // success or danger for toast feedback
            >
              <Toast.Body>{toastMessage}</Toast.Body>
            </Toast>
          </ToastContainer>
        </div>
      </div>
    </div>
  );
}

export default SalesPage;
