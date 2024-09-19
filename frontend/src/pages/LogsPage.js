import React, { useState, useEffect, useCallback } from 'react';
import { Table, Spinner, Row, Col, Button, Form } from 'react-bootstrap';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import api from '../services/api';
import { FaSearch } from 'react-icons/fa';

const LogsPage = ({ showToast }) => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState({
    type: '',
    level: '',
    startDate: null,
    endDate: null,
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(50); // Default items per page
  const [totalPages, setTotalPages] = useState(1);

  // Fetch logs with filters
  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page: currentPage,
        per_page: itemsPerPage,
        type: filter.type,
        level: filter.level,
        start_date: filter.startDate ? filter.startDate.toISOString().split('T')[0] : '',
        end_date: filter.endDate ? filter.endDate.toISOString().split('T')[0] : '',
      };

      const response = await api.get('/logs/', { params });
      setLogs(response.data.logs || []);
      console.log(response.data);
      setTotalPages(response.data.total_pages || 1);
    } catch (error) {
      console.error('Error fetching logs:', error);
      setError('Failed to fetch logs. Please try again later.');
      showToast('danger', 'Failed to fetch logs. Please try again later.', 'Error');
    } finally {
      setLoading(false);
    }
  }, [currentPage, itemsPerPage, filter, showToast]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  // Handle filter submission
  const handleFilter = () => {
    setCurrentPage(1); // Reset to the first page when filtering
    fetchLogs();
  };

  // Handle page change
  const handlePageChange = (pageNumber) => setCurrentPage(pageNumber);

  if (loading) return <Spinner animation="border" />;

  return (
    <div style={{ marginTop: '20px', padding: '20px' }}>
      <Row className="mb-4">
        <Col>
          <h2>Logs</h2>
        </Col>
      </Row>

      {/* Filter Section */}
      <Form className="mb-4">
        <Row>
          <Col md={3}>
            <Form.Control
              as="select"
              value={filter.type}
              onChange={(e) => setFilter({ ...filter, type: e.target.value })}
            >
              <option value="">Select Log Type</option>
              <option value="general">General</option>
              <option value="error">Error</option>
              <option value="success">Success</option>
            </Form.Control>
          </Col>
          <Col md={3}>
            <Form.Control
              as="select"
              value={filter.level}
              onChange={(e) => setFilter({ ...filter, level: e.target.value })}
            >
              <option value="">Select Log Level</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
            </Form.Control>
          </Col>
          <Col md={3}>
            <DatePicker
              selected={filter.startDate}
              onChange={(date) => setFilter({ ...filter, startDate: date })}
              placeholderText="Start Date"
              className="form-control"
            />
          </Col>
          <Col md={3}>
            <DatePicker
              selected={filter.endDate}
              onChange={(date) => setFilter({ ...filter, endDate: date })}
              placeholderText="End Date"
              className="form-control"
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

      {/* Logs Table */}
      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>#</th>
            <th>Timestamp</th>
            <th>Type</th>
            <th>Level</th>
            <th>Message</th>
          </tr>
        </thead>
        <tbody>
          {logs.length > 0 ? (
            logs.map((log, index) => (
              <tr key={log.id}>
                <td>{(currentPage - 1) * itemsPerPage + index + 1}</td>
                <td>{new Date(log.timestamp).toLocaleString()}</td>
                <td>{log.type}</td>
                <td>{log.level}</td>
                <td>{log.message}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="5" className="text-center">No logs found</td>
            </tr>
          )}
        </tbody>
      </Table>

      {/* Pagination Controls */}
      <Row>
        <Col className="text-center">
          {[...Array(totalPages).keys()].map((number) => (
            <Button
              key={number}
              variant={currentPage === number + 1 ? 'primary' : 'secondary'}
              onClick={() => handlePageChange(number + 1)}
              className="mx-1"
            >
              {number + 1}
            </Button>
          ))}
        </Col>
      </Row>
    </div>
  );
};

export default LogsPage;
