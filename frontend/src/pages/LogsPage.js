import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
  const [itemsPerPage] = useState(50);
  const [totalPages, setTotalPages] = useState(1);

  // Fetch logs from the API
  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page: currentPage,
        per_page: itemsPerPage,
        sort_order: 'desc',
        ...(filter.type && { type: filter.type.toLowerCase() }),
        ...(filter.level && { level: filter.level }),
      };

      const response = await api.get('/logs/', { params });
      const fetchedLogs = response.data.logs || [];

      // Set logs and total pages
      setLogs(fetchedLogs);
      setTotalPages(response.data.total_pages || 1);
    } catch (error) {
      console.error('Error fetching logs:', error);
      let errorMessage = 'Failed to fetch logs. Please try again later.';
      if (error.response) {
        errorMessage = error.response.data.message || errorMessage;
      } else if (error.request) {
        errorMessage = 'Network error: Unable to reach the server.';
      }
      setError(errorMessage);
      showToast('danger', errorMessage, 'Error');
    } finally {
      setLoading(false);
    }
  }, [currentPage, itemsPerPage, filter, showToast]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  // Handle filter changes
  const handleFilter = () => {
    if (filter.startDate && filter.endDate && filter.startDate > filter.endDate) {
      showToast('warning', 'Start date must be before end date.', 'Invalid Date Range');
      return;
    }
    setCurrentPage(1); // Reset to first page on filter change
    fetchLogs();
  };

  // Reset filters
  const handleResetFilters = () => {
    setFilter({ type: '', level: '', startDate: null, endDate: null });
    setCurrentPage(1);
    fetchLogs();
  };

  // Change page
  const handlePageChange = (pageNumber) => {
    if (pageNumber < 1 || pageNumber > totalPages) return;
    setCurrentPage(pageNumber);
  };

  // Parse log entry
  const parseLogEntry = (logEntry) => {
    const timestampRegex = /(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},)/;
    const matches = logEntry.match(timestampRegex);

    if (matches) {
      const timestamp = matches[0].replace(',', ''); // Remove the comma
      const message = logEntry.replace(timestampRegex, '').trim();
      const dateObject = new Date(timestamp);
      return {
        timestamp: isNaN(dateObject.getTime()) ? 'Invalid Date' : dateObject,
        message,
      };
    }

    return { timestamp: 'No Timestamp', message: logEntry };
  };

  // Filter logs based on selected date range
  const filteredLogs = useMemo(() => {
    return logs.filter(log => {
      const parsedLog = parseLogEntry(log);
      const logDate = parsedLog.timestamp;
      const startDate = filter.startDate ? new Date(filter.startDate) : null;
      const endDate = filter.endDate ? new Date(filter.endDate) : null;

      return (
        (!startDate || logDate >= startDate) &&
        (!endDate || logDate <= endDate)
      );
    });
  }, [logs, filter]);

  // Memoized parsed logs to avoid re-calculation on every render
  const parsedLogs = useMemo(() => {
    return filteredLogs.map(log => parseLogEntry(log));
  }, [filteredLogs]);

  // Pagination calculation
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

      <Form className="mb-4">
        <Row className="align-items-end">
          <Col xs={12} md={3} lg={2}>
            <Form.Control
              as="select"
              value={filter.type}
              onChange={(e) => setFilter({ ...filter, type: e.target.value.toLowerCase() })}
              aria-label="Log Type"
            >
              <option value="">Log Type</option>
              <option value="general">General</option>
              <option value="error">Error</option>
              <option value="success">Success</option>
            </Form.Control>
          </Col>
          <Col xs={12} md={3} lg={2}>
            <Form.Control
              as="select"
              value={filter.level}
              onChange={(e) => setFilter({ ...filter, level: e.target.value })}
              aria-label="Log Level"
            >
              <option value="">Log Level</option>
              <option value="info">INFO</option>
              <option value="warning">WARNING</option>
              <option value="error">ERROR</option>
            </Form.Control>
          </Col>
          <Col xs={12} md={3} lg={2}>
            <DatePicker
              selected={filter.startDate}
              onChange={(date) => setFilter({ ...filter, startDate: date })}
              placeholderText="Start Date"
              className="form-control"
              aria-label="Start Date"
              showTimeSelect
              dateFormat="Pp"
            />
          </Col>
          <Col xs={12} md={3} lg={2}>
            <DatePicker
              selected={filter.endDate}
              onChange={(date) => setFilter({ ...filter, endDate: date })}
              placeholderText="End Date"
              className="form-control"
              aria-label="End Date"
              showTimeSelect
              dateFormat="Pp"
            />
          </Col>
          <Col xs={12} md={3} lg={2}>
            <Button variant="primary" onClick={handleFilter} aria-label="Filter Logs">
              <FaSearch /> Filter
            </Button>
            <Button variant="secondary" onClick={handleResetFilters} className="ms-2" aria-label="Reset Filters">
              <FaUndo /> Reset
            </Button>
          </Col>
        </Row>
      </Form>

      {error && <p className="text-center text-danger">{error}</p>}
      {loading && <div className="text-center my-3"><Spinner animation="border" aria-label="Loading logs..." /></div>}

      {!loading && (
        <Table striped bordered hover responsive>
          <thead>
            <tr>
              <th>#</th>
              <th>Timestamp</th>
              <th>Message</th>
            </tr>
          </thead>
          <tbody>
            {parsedLogs.length > 0 ? (
              parsedLogs.map((log, index) => (
                <tr key={index}>
                  <td>{(currentPage - 1) * itemsPerPage + index + 1}</td>
                  <td>{typeof log.timestamp === 'string' ? log.timestamp : log.timestamp.toLocaleString()}</td>
                  <td>{log.message}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="3" className="text-center">No logs found</td>
              </tr>
            )}
          </tbody>
        </Table>
      )}

      {!loading && totalPages > 1 && (
        <Row className="mt-3">
          <Col className="text-center">
            {currentPage > 1 && (
              <>
                <Button variant="secondary" onClick={() => handlePageChange(1)} className="mx-1" aria-label="First Page">
                  <FaAngleDoubleLeft />
                </Button>
                <Button variant="secondary" onClick={() => handlePageChange(currentPage - 1)} className="mx-1" aria-label="Previous Page">
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
                aria-label={`Page ${startPage + number}`}
              >
                {startPage + number}
              </Button>
            ))}
            {currentPage < totalPages && (
              <>
                <Button variant="secondary" onClick={() => handlePageChange(currentPage + 1)} className="mx-1" aria-label="Next Page">
                  <FaArrowRight />
                </Button>
                <Button variant="secondary" onClick={() => handlePageChange(totalPages)} className="mx-1" aria-label="Last Page">
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
