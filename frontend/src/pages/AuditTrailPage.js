import React, { useState, useEffect, useCallback } from 'react';
import { Table, Spinner, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import { FaSearch, FaInfoCircle, FaArrowLeft, FaArrowRight, FaAngleDoubleLeft, FaAngleDoubleRight } from 'react-icons/fa';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import api from '../services/api';

const AuditTrailPage = ({ showToast }) => {
  const [auditLogs, setAuditLogs] = useState([]);
  const [users, setUsers] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState({
    resourceType: '',
    action: '',
    startDate: null,
    endDate: null,
  });
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedLog, setSelectedLog] = useState(null);
  const [resourceTypes, setResourceTypes] = useState([]);
  const [actions, setActions] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(50);
  const [archiveView, setArchiveView] = useState('current'); // 'current', 'previous', 'older'

  // Fetch all audit logs
  const fetchAuditLogs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/audit_trail/');
      const logs = response.data || [];
      setAuditLogs(logs);
      extractUniqueResourceTypesAndActions(logs);
    } catch (error) {
      console.error('Error fetching audit logs:', error);
      setError('Failed to fetch audit logs. Please try again later.');
      showToast('danger', 'Failed to fetch audit logs. Please try again later.', 'Error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  // Extract unique resource types and actions from the audit logs
  const extractUniqueResourceTypesAndActions = (logs) => {
    const uniqueResourceTypes = [...new Set(logs.map((log) => log.resource_type))];
    const uniqueActions = [...new Set(logs.map((log) => log.action.replace('AuditAction.', '')))];
    setResourceTypes(uniqueResourceTypes);
    setActions(uniqueActions);
  };

  // Fetch all users to map user IDs to names
  const fetchUsers = useCallback(async () => {
    try {
      const response = await api.get('/users/');
      const usersMap = {};
      response.data.users.forEach((user) => {
        usersMap[user.id] = user.name;
      });
      setUsers(usersMap);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  }, []);

  useEffect(() => {
    fetchAuditLogs();
    fetchUsers();
  }, [fetchAuditLogs, fetchUsers]);

  // Handle filtering
  const handleFilter = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/audit_trail/filter', filter);
      const logs = response.data || [];
      setAuditLogs(logs);
      extractUniqueResourceTypesAndActions(logs);
      setCurrentPage(1); // Reset to the first page after filtering
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

  // Calculate the current logs to display based on pagination and archive view
  const filteredLogs = auditLogs.filter((log) => {
    const logDate = new Date(log.timestamp);
    const today = new Date();
    if (archiveView === 'current') {
      return logDate >= new Date(today.setDate(today.getDate() - today.getDay())); // Current week
    } else if (archiveView === 'previous') {
      return (
        logDate < new Date(today.setDate(today.getDate() - today.getDay())) &&
        logDate >= new Date(today.setDate(today.getDate() - 7))
      ); // Previous week
    } else {
      return logDate < new Date(today.setDate(today.getDate() - 7)); // Older than previous week
    }
  });

  const indexOfLastLog = currentPage * itemsPerPage;
  const indexOfFirstLog = indexOfLastLog - itemsPerPage;
  const currentLogs = filteredLogs.slice(indexOfFirstLog, indexOfLastLog);

  // Handle page change
  const handlePageChange = (pageNumber) => setCurrentPage(pageNumber);

  // Calculate the number of pages to show in pagination
  const totalPages = Math.ceil(filteredLogs.length / itemsPerPage);
  const maxPageNumbers = 5;
  const startPage = Math.max(1, currentPage - Math.floor(maxPageNumbers / 2));
  const endPage = Math.min(totalPages, startPage + maxPageNumbers - 1);

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
        <Row className="align-items-end">
          <Col md={2}>
            <Form.Control
              as="select"
              value={filter.resourceType}
              onChange={(e) => setFilter({ ...filter, resourceType: e.target.value })}
            >
              <option value="">Resource Type</option>
              {resourceTypes.map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </Form.Control>
          </Col>
          <Col md={2}>
            <Form.Control
              as="select"
              value={filter.action}
              onChange={(e) => setFilter({ ...filter, action: e.target.value })}
            >
              <option value="">Action</option>
              {actions.map((action) => (
                <option key={action} value={action}>{action}</option>
              ))}
            </Form.Control>
          </Col>
          <Col md={2}>
            <DatePicker
              selected={filter.startDate}
              onChange={(date) => setFilter({ ...filter, startDate: date })}
              placeholderText="Start Date"
              className="form-control"
            />
          </Col>
          <Col md={2}>
            <DatePicker
              selected={filter.endDate}
              onChange={(date) => setFilter({ ...filter, endDate: date })}
              placeholderText="End Date"
              className="form-control"
            />
          </Col>
          <Col md={2}>
            <Button variant="primary" onClick={handleFilter}>
              <FaSearch /> Filter
            </Button>
          </Col>
        </Row>
      </Form>

      {error && <p className="text-center text-danger">{error}</p>}

      {/* Archive Toggle */}
      <Row className="mb-4">
        <Col>
          <Button variant={archiveView === 'current' ? 'primary' : 'secondary'} onClick={() => setArchiveView('current')}>
            Current Week
          </Button>{' '}
          <Button variant={archiveView === 'previous' ? 'primary' : 'secondary'} onClick={() => setArchiveView('previous')}>
            Previous Week
          </Button>{' '}
          <Button variant={archiveView === 'older' ? 'primary' : 'secondary'} onClick={() => setArchiveView('older')}>
            Older
          </Button>
        </Col>
      </Row>

      {/* Audit Logs Table */}
      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>#</th>
            <th>Resource Type</th>
            <th>Action</th>
            <th>User</th>
            <th>Resource ID</th>
            <th>Details</th>
            <th>Date</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {currentLogs.length > 0 ? (
            currentLogs.map((log, index) => (
              <tr key={log.id}>
                <td>{indexOfFirstLog + index + 1}</td>
                <td>{log.resource_type}</td>
                <td>{log.action.replace('AuditAction.', '')}</td>
                <td>{users[log.user_id] || 'Unknown User'}</td>
                <td>{log.resource_id || 'N/A'}</td>
                <td>{log.details}</td>
                <td>{new Date(log.timestamp).toLocaleString()}</td>
                <td>
                  <Button variant="link" size="sm" onClick={() => handleViewDetails(log.id)}>
                    <FaInfoCircle /> Details
                  </Button>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="8" className="text-center">No audit logs found</td>
            </tr>
          )}
        </tbody>
      </Table>

      {/* Pagination Controls */}
      <Row className="mt-3">
        <Col className="text-center">
          {currentPage > 1 && (
            <>
              <Button variant="secondary" onClick={() => handlePageChange(1)} className="mx-1">
                <FaAngleDoubleLeft />
              </Button>
              <Button variant="secondary" onClick={() => handlePageChange(currentPage - 1)} className="mx-1">
                <FaArrowLeft />
              </Button>
            </>
          )}
          {[...Array(endPage - startPage + 1).keys()].map((number) => (
            <Button
              key={startPage + number}
              variant={currentPage === startPage + number ? 'primary' : 'secondary'}
              onClick={() => handlePageChange(startPage + number)}
              className="mx-1"
            >
              {startPage + number}
            </Button>
          ))}
          {currentPage < totalPages && (
            <>
              <Button variant="secondary" onClick={() => handlePageChange(currentPage + 1)} className="mx-1">
                <FaArrowRight />
              </Button>
              <Button variant="secondary" onClick={() => handlePageChange(totalPages)} className="mx-1">
                <FaAngleDoubleRight />
              </Button>
            </>
          )}
        </Col>
      </Row>

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
              <p><strong>Action:</strong> {selectedLog.action.replace('AuditAction.', '')}</p>
              <p><strong>User:</strong> {users[selectedLog.user_id] || 'Unknown User'}</p>
              <p><strong>Resource ID:</strong> {selectedLog.resource_id || 'N/A'}</p>
              <p><strong>Date:</strong> {new Date(selectedLog.timestamp).toLocaleString()}</p>
              <p><strong>Details:</strong> {selectedLog.details}</p>
              <p><strong>IP Address:</strong> {selectedLog.ip_address || 'N/A'}</p>
              <p><strong>User Agent:</strong> {selectedLog.user_agent || 'N/A'}</p>
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
