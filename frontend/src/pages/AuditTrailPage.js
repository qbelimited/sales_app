import React, { useState, useEffect, useCallback } from 'react';
import { Table, Spinner, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import { FaSearch, FaInfoCircle } from 'react-icons/fa';
import api from '../services/api';

const AuditTrailPage = ({ showToast }) => {
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState({
    resourceType: '',
    action: '',
    startDate: '',
    endDate: '',
  });
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedLog, setSelectedLog] = useState(null);
  const [resourceTypes, setResourceTypes] = useState([]);

  // Fetch all audit logs
  const fetchAuditLogs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/audit_trail/');
      setAuditLogs(response.data || []);
      console.log('Audit logs:', response.data);
    } catch (error) {
      console.error('Error fetching audit logs:', error);
      setError('Failed to fetch audit logs. Please try again later.');
      showToast('danger', 'Failed to fetch audit logs. Please try again later.', 'Error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchAuditLogs();
  }, [fetchAuditLogs]);

  // Fetch resource types (assuming an endpoint or static list)
  useEffect(() => {
    // Assuming you have an endpoint to get resource types, otherwise use a static list
    const fetchResourceTypes = async () => {
      try {
        // const response = await api.get('/resource_types/'); // Update with your actual endpoint if needed
        // setResourceTypes(response.data || []);
        // console.log('Resource types:', response.data);
      } catch (error) {
        console.error('Error fetching resource types:', error);
      }
    };
    fetchResourceTypes();
  }, []);

  // Handle filtering
  const handleFilter = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/audit_trail/filter', filter);
      setAuditLogs(response.data || []);
    } catch (error) {
      console.error('Error filtering audit logs:', error);
      setError('Failed to filter audit logs. Please try again later.');
      showToast('danger', 'Failed to filter audit logs. Please try again later.', 'Error');
    } finally {
      setLoading(false);
    }
  };

  // Handle viewing details of a specific log
  const handleViewDetails = async (logId) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/audit_trail/${logId}`);
      setSelectedLog(response.data);
      setShowDetailsModal(true);
    } catch (error) {
      console.error('Error fetching log details:', error);
      showToast('danger', 'Failed to fetch log details. Please try again later.', 'Error');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Spinner animation="border" />;

  return (
    <div style={{ marginTop: '20px', padding: '20px' }}>
      <Row className="mb-4">
        <Col>
          <h2>Audit Trail</h2>
        </Col>
      </Row>

      {/* Filter Section */}
      <Form className="mb-4">
        <Row>
          <Col md={3}>
            <Form.Control
              as="select"
              value={filter.resourceType}
              onChange={(e) => setFilter({ ...filter, resourceType: e.target.value })}
            >
              <option value="">Select Resource Type</option>
              {resourceTypes.map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </Form.Control>
          </Col>
          <Col md={3}>
            <Form.Control
              type="text"
              placeholder="Action"
              value={filter.action}
              onChange={(e) => setFilter({ ...filter, action: e.target.value })}
            />
          </Col>
          <Col md={3}>
            <Form.Control
              type="date"
              placeholder="Start Date"
              value={filter.startDate}
              onChange={(e) => setFilter({ ...filter, startDate: e.target.value })}
            />
          </Col>
          <Col md={3}>
            <Form.Control
              type="date"
              placeholder="End Date"
              value={filter.endDate}
              onChange={(e) => setFilter({ ...filter, endDate: e.target.value })}
            />
          </Col>
        </Row>
        <Row className="mt-3">
          <Col>
            <Button variant="primary" onClick={handleFilter}>
              <FaSearch /> Filter
            </Button>
          </Col>
        </Row>
      </Form>

      {error && <p className="text-center text-danger">{error}</p>}

      {/* Audit Logs Table */}
      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>#</th>
            <th>Resource Type</th>
            <th>Action</th>
            <th>Performed By</th>
            <th>Date</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {auditLogs.length > 0 ? (
            auditLogs.map((log, index) => (
              <tr key={log.id}>
                <td>{index + 1}</td>
                <td>{log.resource_type}</td>
                <td>{log.action}</td>
                <td>{log.performed_by}</td>
                <td>{new Date(log.date).toLocaleString()}</td>
                <td>
                  <Button variant="link" size="sm" onClick={() => handleViewDetails(log.id)}>
                    <FaInfoCircle /> Details
                  </Button>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="6" className="text-center">No audit logs found</td>
            </tr>
          )}
        </tbody>
      </Table>

      {/* View Details Modal */}
      <Modal show={showDetailsModal} onHide={() => setShowDetailsModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Audit Log Details</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedLog ? (
            <>
              <p><strong>ID:</strong> {selectedLog.id}</p>
              <p><strong>Resource Type:</strong> {selectedLog.resource_type}</p>
              <p><strong>Action:</strong> {selectedLog.action}</p>
              <p><strong>Performed By:</strong> {selectedLog.performed_by}</p>
              <p><strong>Date:</strong> {new Date(selectedLog.date).toLocaleString()}</p>
              <p><strong>Description:</strong> {selectedLog.description}</p>
            </>
          ) : (
            <p>No details available.</p>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDetailsModal(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default AuditTrailPage;
