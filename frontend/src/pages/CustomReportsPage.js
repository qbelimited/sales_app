import React, { useState, useEffect } from 'react';
import { Table, Button, Form, Modal, Spinner } from 'react-bootstrap';
import api from '../services/api';

const CustomReportsPage = ({ showToast }) => {
  const [reports, setReports] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [modalData, setModalData] = useState({ name: '', fields: [], groupBy: '', aggregations: {}, filters: {} });
  const [loading, setLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    fetchCustomReports();
  }, []);

  const fetchCustomReports = async () => {
    setLoading(true);
    try {
      const response = await api.get('/reports/custom');
      setReports(response.data);
    } catch (error) {
      showToast('danger', 'Failed to fetch custom reports.', 'Error');
    } finally {
      setLoading(false);
    }
  };

  const handleShowModal = (report = null) => {
    setIsEditing(!!report);
    setModalData(report || { name: '', fields: [], groupBy: '', aggregations: {}, filters: {} });
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
  };

  const handleSaveReport = async () => {
    setLoading(true);
    try {
      if (isEditing) {
        await api.put(`/reports/custom?report_id=${modalData.id}`, modalData);
        showToast('success', 'Custom report updated successfully.', 'Success');
      } else {
        await api.post('/reports/custom', modalData);
        showToast('success', 'Custom report created successfully.', 'Success');
      }
      fetchCustomReports();
      handleCloseModal();
    } catch (error) {
      showToast('danger', 'Failed to save custom report.', 'Error');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteReport = async (reportId) => {
    setLoading(true);
    try {
      await api.delete(`/reports/custom?report_id=${reportId}`);
      showToast('success', 'Custom report deleted successfully.', 'Success');
      fetchCustomReports();
    } catch (error) {
      showToast('danger', 'Failed to delete custom report.', 'Error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mt-5">
      <h2>Manage Custom Reports</h2>
      <Button variant="primary" onClick={() => handleShowModal()}>
        Create Custom Report
      </Button>

      {loading ? (
        <Spinner animation="border" />
      ) : (
        <Table striped bordered hover className="mt-3">
          <thead>
            <tr>
              <th>Name</th>
              <th>Fields</th>
              <th>Group By</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((report) => (
              <tr key={report.id}>
                <td>{report.name}</td>
                <td>{JSON.stringify(report.fields)}</td>
                <td>{report.groupBy}</td>
                <td>
                  <Button variant="info" onClick={() => handleShowModal(report)}>Edit</Button>
                  <Button variant="danger" onClick={() => handleDeleteReport(report.id)}>Delete</Button>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      {/* Modal for creating/updating custom reports */}
      <Modal show={showModal} onHide={handleCloseModal}>
        <Modal.Header closeButton>
          <Modal.Title>{isEditing ? 'Edit Custom Report' : 'Create Custom Report'}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group controlId="formReportName">
              <Form.Label>Report Name</Form.Label>
              <Form.Control
                type="text"
                value={modalData.name}
                onChange={(e) => setModalData({ ...modalData, name: e.target.value })}
                required
              />
            </Form.Group>
            <Form.Group controlId="formReportFields">
              <Form.Label>Fields</Form.Label>
              <Form.Control
                type="text"
                value={JSON.stringify(modalData.fields)}
                onChange={(e) => setModalData({ ...modalData, fields: JSON.parse(e.target.value) })}
                placeholder="Enter fields as JSON array"
                required
              />
            </Form.Group>
            <Form.Group controlId="formReportGroupBy">
              <Form.Label>Group By</Form.Label>
              <Form.Control
                type="text"
                value={modalData.groupBy}
                onChange={(e) => setModalData({ ...modalData, groupBy: e.target.value })}
              />
            </Form.Group>
            <Form.Group controlId="formReportAggregations">
              <Form.Label>Aggregations</Form.Label>
              <Form.Control
                type="text"
                value={JSON.stringify(modalData.aggregations)}
                onChange={(e) => setModalData({ ...modalData, aggregations: JSON.parse(e.target.value) })}
                placeholder="Enter aggregations as JSON object"
              />
            </Form.Group>
            <Form.Group controlId="formReportFilters">
              <Form.Label>Filters</Form.Label>
              <Form.Control
                type="text"
                value={JSON.stringify(modalData.filters)}
                onChange={(e) => setModalData({ ...modalData, filters: JSON.parse(e.target.value) })}
                placeholder="Enter filters as JSON object"
              />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseModal}>Close</Button>
          <Button variant="primary" onClick={handleSaveReport}>
            {loading ? <Spinner animation="border" size="sm" /> : isEditing ? 'Update Report' : 'Create Report'}
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default CustomReportsPage;
