import React, { useState, useEffect } from 'react';
import SalesForm from '../components/SalesForm';
import SalesTable from '../components/SalesTable';
import { Button, Toast, ToastContainer, Spinner } from 'react-bootstrap';
import api from '../services/api';  // Import Axios instance or your API service

function SalesPage() {
  const [salesRecords, setSalesRecords] = useState([]);
  const [loading, setLoading] = useState(true);  // Loading state for fetching data
  const [showForm, setShowForm] = useState(false); // State to control form visibility
  const [currentSale, setCurrentSale] = useState(null); // State to track the sale being edited
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [toastVariant, setToastVariant] = useState(''); // success or danger for toast feedback

  // Fetch sales records from API on component mount
  useEffect(() => {
    const fetchSales = async () => {
      try {
        const response = await api.get('/sales');  // Replace with your actual API endpoint
        setSalesRecords(response.data);
        setLoading(false);
      } catch (error) {
        showToastMessage('danger', 'Error fetching sales records.');
        setLoading(false);
      }
    };

    fetchSales();
  }, []);

  // Reusable function to show toast messages
  const showToastMessage = (variant, message) => {
    setToastMessage(message);
    setToastVariant(variant);
    setShowToast(true);
  };

  // Function to handle form submission (for both new sale and edit)
  const handleFormSubmit = async (newSale) => {
    if (currentSale) {
      // Update existing sale via API
      try {
        await api.put(`/sales/${currentSale.id}`, newSale);
        setSalesRecords(
          salesRecords.map((sale) =>
            sale.id === currentSale.id ? { ...sale, ...newSale } : sale
          )
        );
        showToastMessage('success', 'Sale record updated successfully!');
      } catch (error) {
        showToastMessage('danger', 'Error updating sale record.');
      }
    } else {
      // Add new sale via API
      try {
        const response = await api.post('/sales', newSale);  // Send the new sale to the API
        setSalesRecords([...salesRecords, { id: response.data.id, ...newSale }]);
        showToastMessage('success', 'Sale record added successfully!');
      } catch (error) {
        showToastMessage('danger', 'Error adding new sale record.');
      }
    }

    setShowForm(false);
    setCurrentSale(null); // Clear the current sale after submission
  };

  // Function to handle editing a sale
  const handleEdit = (sale) => {
    setCurrentSale(sale); // Set the sale to be edited
    setShowForm(true); // Show the form with sale data
  };

  // Function to handle deleting a sale
  const handleDelete = async (saleId) => {
    if (!window.confirm('Are you sure you want to delete this sale?')) return;

    try {
      await api.delete(`/sales/${saleId}`);  // Delete the sale via API
      setSalesRecords(salesRecords.filter(sale => sale.id !== saleId));
      showToastMessage('success', 'Sale record deleted successfully!');
    } catch (error) {
      showToastMessage('danger', 'Error deleting sale record.');
    }
  };

  // Show loading spinner while fetching data
  if (loading) {
    return (
      <div className="text-center mt-5">
        <Spinner animation="border" />
      </div>
    );
  }

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
