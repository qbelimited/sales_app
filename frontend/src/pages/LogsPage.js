import React, { useState, useEffect, useCallback } from 'react';
import { Table, Spinner, Row, Col, Button, Form } from 'react-bootstrap';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import api from '../services/api';
import { FaSearch, FaArrowLeft, FaArrowRight, FaAngleDoubleLeft, FaAngleDoubleRight, FaUndo } from 'react-icons/fa';

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
        ...(filter.type && { type: filter.type }),
        ...(filter.level && { level: filter.level }),
        ...(filter.startDate && { start_date: filter.startDate.toISOString().split('T')[0] }),
        ...(filter.endDate && { end_date: filter.endDate.toISOString().split('T')[0] }),
      };

      const response = await api.get('/logs/', { params });
      setLogs(response.data.logs || []);
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

  // Handle reset filters
  const handleResetFilters = () => {
    setFilter({
      type: '',
      level: '',
      startDate: null,
      endDate: null,
    });
    setCurrentPage(1);
    fetchLogs();
  };

  // Handle page change
  const handlePageChange = (pageNumber) => setCurrentPage(pageNumber);

  // Calculate pagination range
  const maxPageNumbers = 5;
  const startPage = Math.max(1, currentPage - Math.floor(maxPageNumbers / 2));
  const endPage = Math.min(totalPages, startPage + maxPageNumbers - 1);

  return (
    <div style={{ marginTop: '20px', padding: '20px' }}>
      <Row className="mb-4">
        <Col>
          <h2>Logs</h2>
        </Col>
      </Row>

      {/* Filter Section */}
      <Form className="mb-4">
        <Row className="align-items-end">
          <Col md={2}>
            <Form.Control
              as="select"
              value={filter.type}
              onChange={(e) => setFilter({ ...filter, type: e.target.value })}
            >
              <option value="">Log Type</option>
              <option value="general">General</option>
              <option value="error">Error</option>
              <option value="success">Success</option>
            </Form.Control>
          </Col>
          <Col md={2}>
            <Form.Control
              as="select"
              value={filter.level}
              onChange={(e) => setFilter({ ...filter, level: e.target.value })}
            >
              <option value="">Log Level</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
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
            <Button variant="secondary" onClick={handleResetFilters} className="ms-2">
              <FaUndo /> Reset
            </Button>
          </Col>
        </Row>
      </Form>

      {error && <p className="text-center text-danger">{error}</p>}

      {/* Loading Spinner */}
      {loading && <div className="text-center my-3"><Spinner animation="border" /></div>}

      {/* Logs Table */}
      {!loading && (
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
                <tr key={log.id || index}>
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
      )}

      {/* Pagination Controls */}
      {!loading && totalPages > 1 && (
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
      )}
    </div>
  );
};

export default LogsPage;
