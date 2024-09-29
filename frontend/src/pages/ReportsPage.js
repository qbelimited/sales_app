import React, { useState, useEffect } from 'react';
import { Table, Button, Form, Row, Col, Spinner, Modal } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom'; // Import useNavigate for navigation
import api from '../services/api';

const ReportsPage = ({ showToast }) => {
  const navigate = useNavigate(); // Create a navigate instance for navigation
  const [filters, setFilters] = useState({ startDate: null, endDate: null, reportType: '' });
  const [previewData, setPreviewData] = useState([]); // Initialize as an empty array
  const [loading, setLoading] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportTypes, setReportTypes] = useState([]);

  useEffect(() => {
    // Fetch available report types when the component mounts
    const fetchReportTypes = async () => {
      try {
        const response = await api.get('/reports/report-types');
        setReportTypes(response.data);
      } catch (error) {
        showToast('danger', 'Failed to fetch report types.', 'Error');
      }
    };

    fetchReportTypes();
  }, [showToast]);

  const handlePreview = async () => {
    if (!filters.startDate || !filters.endDate || !filters.reportType) {
      showToast('warning', 'Please fill in all required fields.', 'Warning');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/reports/generate', {
        report_type: filters.reportType,
        filters: {
          startDate: filters.startDate,
          endDate: filters.endDate,
        },
      });

      // Check if response.data is an array
      if (Array.isArray(response.data)) {
        setPreviewData(response.data);
        console.log("Preview data:", response.data);
        setShowPreview(true); // Show the modal if data is available
      } else {
        showToast('info', 'No data found for the selected filters.', 'Info');
        setPreviewData([]); // Reset previewData to an empty array
      }
    } catch (error) {
      console.error("Error fetching preview data:", error); // Log the error for debugging
      showToast('danger', 'Failed to fetch preview data.', 'Error');
      setPreviewData([]); // Ensure previewData is reset
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async (format) => {
    setReportLoading(true);
    try {
      const response = await api.post('/reports/generate', {
        report_type: filters.reportType,
        filters: {
          startDate: filters.startDate,
          endDate: filters.endDate,
        },
        format,
      });

      // Check if the response is for a downloadable file
      if (response.data && response.data.url) {
        window.open(response.data.url, '_blank'); // Open the report in a new tab
        showToast('success', 'Report generated successfully.', 'Success');
      } else {
        showToast('danger', 'Failed to generate report. No valid URL returned.', 'Error');
      }
    } catch (error) {
      showToast('danger', 'Failed to generate report.', 'Error');
    } finally {
      setReportLoading(false);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((prev) => ({ ...prev, [name]: value }));
  };

  return (
    <div className="container mt-5">
      <h2>Generate Reports</h2>

      <Form>
        <Row>
          <Col>
            <Form.Group controlId="filterStartDate">
              <Form.Label>Start Date</Form.Label>
              <Form.Control type="date" name="startDate" onChange={handleFilterChange} />
            </Form.Group>
          </Col>
          <Col>
            <Form.Group controlId="filterEndDate">
              <Form.Label>End Date</Form.Label>
              <Form.Control type="date" name="endDate" onChange={handleFilterChange} />
            </Form.Group>
          </Col>
          <Col>
            <Form.Group controlId="reportType">
              <Form.Label>Report Type</Form.Label>
              <Form.Control as="select" name="reportType" onChange={handleFilterChange}>
                <option value="">Select Report Type</option>
                {reportTypes.map((type) => (
                  <option key={type} value={type}>{type.replace(/_/g, ' ').toUpperCase()}</option>
                ))}
              </Form.Control>
            </Form.Group>
          </Col>
          <Col className="align-self-end">
            <Button variant="primary" onClick={handlePreview} disabled={loading}>
              {loading ? <Spinner animation="border" size="sm" /> : 'Preview'}
            </Button>
          </Col>
        </Row>
      </Form>

      {/* Button to navigate to Custom Reports Page */}
      <Button variant="secondary" onClick={() => navigate('/custom-reports')} className="mt-3">
        Manage Custom Reports
      </Button>

      {/* Preview Modal */}
      <Modal show={showPreview} onHide={() => setShowPreview(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Report Preview</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {previewData.length > 0 ? (
            <Table striped bordered hover>
              <thead>
                <tr>
                  {Object.keys(previewData[0]).map((key) => (
                    <th key={key}>{key}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {previewData.map((row, index) => (
                  <tr key={index}>
                    {Object.values(row).map((value, idx) => (
                      <td key={idx}>{value}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </Table>
          ) : (
            <p>No preview data available.</p>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowPreview(false)}>Close</Button>
          <Button variant="primary" onClick={() => handleGenerateReport('xls')} disabled={reportLoading}>
            {reportLoading ? <Spinner animation="border" size="sm" /> : 'Download XLS'}
          </Button>
          <Button variant="primary" onClick={() => handleGenerateReport('pdf')} disabled={reportLoading}>
            {reportLoading ? <Spinner animation="border" size="sm" /> : 'Download PDF'}
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default ReportsPage;
