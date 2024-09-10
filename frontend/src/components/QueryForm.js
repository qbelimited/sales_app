import React, { useState, useEffect, useCallback } from 'react';
import { Table, Button, Pagination, Spinner, Form, Row, Col } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEdit, faTrash, faSort, faSortUp, faSortDown } from '@fortawesome/free-solid-svg-icons';
import api from '../services/api';  // Import the API service
import { debounce } from 'lodash';  // Import lodash for debouncing
import DatePicker from 'react-datepicker'; // React Datepicker for selecting date ranges
import 'react-datepicker/dist/react-datepicker.css'; // Datepicker CSS

const QueryForm = ({ onEdit, onDelete, userRole, userId }) => {
  const [queryRecords, setQueryRecords] = useState([]);
  const [loading, setLoading] = useState(true); // Loading state for API calls
  const [sortConfig, setSortConfig] = useState({ key: 'client_name', direction: 'asc' }); // Sorting state with default
  const [page, setPage] = useState(1); // Current page for pagination
  const [totalPages, setTotalPages] = useState(1); // Total pages available from API
  const [filters, setFilters] = useState({ startDate: null, endDate: null, clientName: '' }); // Date range and other filters

  const limit = 10; // Items per page
  const maxPageDisplay = 5; // Limit the number of pages displayed

  // Function to fetch query records with pagination, sorting, and filtering
  const fetchQueryRecords = async (currentPage, sortKey, sortDirection, filterParams) => {
    setLoading(true);
    try {
      const params = {
        page: currentPage,
        limit,
        sort_by: sortKey,
        sort_direction: sortDirection,
        ...filterParams, // Add filter parameters (date range and client name)
      };

      // Check user role to filter queries based on role
      if (userRole === 'query_manager') {
        params.query_manager_id = userId; // Only fetch queries by this user
      }

      const response = await api.get('/queries', { params });
      setQueryRecords(response.data.records); // Assume the API returns query records in "records"
      setTotalPages(response.data.total_pages); // Assume total pages are returned in "total_pages"
      setLoading(false);
    } catch (error) {
      console.error('Error fetching query records:', error);
      setLoading(false);
    }
  };

  // Debounced sorting function to avoid frequent API calls
  const debouncedFetchQueries = useCallback(debounce(fetchQueryRecords, 300), []);

  // Handle sorting changes
  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc'; // Toggle direction
    }
    setSortConfig({ key, direction });
    debouncedFetchQueries(page, key, direction, filters); // Pass filters to API call
  };

  // Handle page changes in pagination
  const handlePageChange = (pageNumber) => {
    setPage(pageNumber);
    fetchQueryRecords(pageNumber, sortConfig.key, sortConfig.direction, filters); // Fetch records for the selected page with filters
  };

  // Handle date range and client name filter submission
  const handleFilterSubmit = (e) => {
    e.preventDefault();
    fetchQueryRecords(page, sortConfig.key, sortConfig.direction, filters); // Fetch records with filters
  };

  // Handle input change for filters
  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((prevFilters) => ({ ...prevFilters, [name]: value }));
  };

  // Get the correct icon for sorting based on the selected column
  const getSortIcon = (key) => {
    if (sortConfig.key === key) {
      return sortConfig.direction === 'asc' ? (
        <FontAwesomeIcon icon={faSortUp} />
      ) : (
        <FontAwesomeIcon icon={faSortDown} />
      );
    }
    return <FontAwesomeIcon icon={faSort} />; // Neutral icon for sortable columns
  };

  // Fetch initial data on mount and when sorting config or page changes
  useEffect(() => {
    fetchQueryRecords(page, sortConfig.key, sortConfig.direction, filters);
  }, [page, sortConfig]);

  // Generate pagination items with limited number of pages
  const renderPaginationItems = () => {
    const pages = [];
    const startPage = Math.max(1, page - Math.floor(maxPageDisplay / 2));
    const endPage = Math.min(totalPages, startPage + maxPageDisplay - 1);

    for (let i = startPage; i <= endPage; i++) {
      pages.push(
        <Pagination.Item key={i} active={i === page} onClick={() => handlePageChange(i)}>
          {i}
        </Pagination.Item>
      );
    }
    return pages;
  };

  if (loading) {
    return (
      <div className="text-center mt-5">
        <Spinner animation="border" />
      </div>
    );
  }

  return (
    <div className="mt-5">
      <h2>Current Queries</h2>

      {/* Filter Section */}
      <Form onSubmit={handleFilterSubmit} className="mb-4">
        <Row>
          <Col>
            <Form.Group controlId="filterStartDate">
              <Form.Label>Start Date</Form.Label>
              <DatePicker
                selected={filters.startDate}
                onChange={(date) => setFilters((prev) => ({ ...prev, startDate: date }))}
                className="form-control"
                isClearable
              />
            </Form.Group>
          </Col>
          <Col>
            <Form.Group controlId="filterEndDate">
              <Form.Label>End Date</Form.Label>
              <DatePicker
                selected={filters.endDate}
                onChange={(date) => setFilters((prev) => ({ ...prev, endDate: date }))}
                className="form-control"
                isClearable
              />
            </Form.Group>
          </Col>
          <Col>
            <Form.Group controlId="filterClientName">
              <Form.Label>Client Name</Form.Label>
              <Form.Control
                type="text"
                name="clientName"
                value={filters.clientName}
                onChange={handleFilterChange}
                placeholder="Enter client name"
              />
            </Form.Group>
          </Col>
          <Col className="align-self-end">
            <Button variant="primary" type="submit">
              Filter
            </Button>
          </Col>
        </Row>
      </Form>

      <Table striped bordered hover responsive className="mt-3">
        <thead>
          <tr>
            <th>#</th>
            <th onClick={() => handleSort('client_name')}>
              Client Name {getSortIcon('client_name')}
            </th>
            <th onClick={() => handleSort('client_id_no')}>
              Client ID {getSortIcon('client_id_no')}
            </th>
            <th onClick={() => handleSort('query_type')}>
              Query Type {getSortIcon('query_type')}
            </th>
            <th onClick={() => handleSort('status')}>
              Status {getSortIcon('status')}
            </th>
            <th onClick={() => handleSort('date_of_query')}>
              Date of Query {getSortIcon('date_of_query')}
            </th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {queryRecords.length > 0 ? (
            queryRecords.map((query, index) => (
              <tr key={query.id}>
                <td>{(page - 1) * limit + index + 1}</td> {/* Adjust for pagination */}
                <td>{query.client_name}</td>
                <td>{query.client_id_no}</td>
                <td>{query.query_type}</td>
                <td>{query.status}</td>
                <td>{new Date(query.date_of_query).toLocaleDateString()}</td>
                <td>
                  <Button
                    variant="warning"
                    size="sm"
                    className="me-2"
                    onClick={() => onEdit(query)}
                  >
                    <FontAwesomeIcon icon={faEdit} />
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => onDelete(query.id)}
                  >
                    <FontAwesomeIcon icon={faTrash} />
                  </Button>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="7" className="text-center">
                No query records available.
              </td>
            </tr>
          )}
        </tbody>
      </Table>

      {/* Pagination Component */}
      <Pagination className="justify-content-center mt-4">
        <Pagination.First onClick={() => handlePageChange(1)} disabled={page === 1} />
        <Pagination.Prev onClick={() => handlePageChange(page - 1)} disabled={page === 1} />
        {renderPaginationItems()}
        <Pagination.Next onClick={() => handlePageChange(page + 1)} disabled={page === totalPages} />
        <Pagination.Last onClick={() => handlePageChange(totalPages)} disabled={page === totalPages} />
      </Pagination>
    </div>
  );
};

export default QueryForm;
