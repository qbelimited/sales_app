import React, { useState, useEffect, useCallback } from 'react';
import { Table, Button, Pagination, Spinner, Form, Row, Col, Modal } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEdit, faTrash, faSort, faSortUp, faSortDown } from '@fortawesome/free-solid-svg-icons';
import api from '../services/api';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

const SalesTable = ({ userRole, userId }) => {
  const [salesRecords, setSalesRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortConfig, setSortConfig] = useState({ key: 'client_name', direction: 'asc' });
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({ startDate: null, endDate: null, clientName: '' });
  const [showModal, setShowModal] = useState(false);
  const [currentSale, setCurrentSale] = useState(null);

  const limit = 10;
  const maxPageDisplay = 5;

  const fetchSalesRecords = useCallback(async (currentPage, sortKey, sortDirection, filterParams) => {
    setLoading(true);
    try {
      const params = {
        page: currentPage,
        limit,
        sort_by: sortKey,
        sort_direction: sortDirection,
        ...filterParams,
      };

      if (userRole === 'sales_manager') {
        params.sales_manager_id = userId;
      }

      const response = await api.get('/sales', { params });
      setSalesRecords(response.data.records || []);
      setTotalPages(response.data.total_pages || 1);
    } catch (error) {
      console.error('Error fetching sales records:', error);
    } finally {
      setLoading(false);
    }
  }, [userRole, userId, limit]);

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const handlePageChange = (pageNumber) => {
    if (pageNumber >= 1 && pageNumber <= totalPages) {
      setPage(pageNumber);
    }
  };

  const handleFilterSubmit = (e) => {
    e.preventDefault();
    fetchSalesRecords(page, sortConfig.key, sortConfig.direction, filters);
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((prevFilters) => ({ ...prevFilters, [name]: value }));
  };

  const handleEdit = (sale) => {
    setCurrentSale(sale);
    setShowModal(true);
  };

  const handleDelete = async (saleId) => {
    if (!window.confirm('Are you sure you want to delete this sale?')) return;
    try {
      await api.delete(`/sales/${saleId}`);
      setSalesRecords(salesRecords.filter((sale) => sale.id !== saleId));
    } catch (error) {
      console.error('Error deleting sale:', error);
    }
  };

  const getSortIcon = (key) => {
    if (sortConfig.key === key) {
      return sortConfig.direction === 'asc' ? (
        <FontAwesomeIcon icon={faSortUp} />
      ) : (
        <FontAwesomeIcon icon={faSortDown} />
      );
    }
    return <FontAwesomeIcon icon={faSort} />;
  };

  useEffect(() => {
    fetchSalesRecords(page, sortConfig.key, sortConfig.direction, filters);
  }, [page, sortConfig, filters, fetchSalesRecords]);

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

   // Handle loading state with Spinner
   if (loading) {
    return (
      <div className="text-center mt-5">
        <Spinner animation="border" />
      </div>
    );
  }

  return (
    <div className="mt-5">
      <h2>Current Sales</h2>

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

      {/* Sales Table */}
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
            <th onClick={() => handleSort('client_phone')}>
              Phone {getSortIcon('client_phone')}
            </th>
            <th onClick={() => handleSort('amount')}>
              Amount {getSortIcon('amount')}
            </th>
            <th onClick={() => handleSort('policy_type_name')}>
              Policy Type {getSortIcon('policy_type_name')}
            </th>
            <th onClick={() => handleSort('serial_number')}>
              Serial Number {getSortIcon('serial_number')}
            </th>
            <th onClick={() => handleSort('sale_manager')}>
              Sales Manager {getSortIcon('sale_manager')}
            </th>
            <th onClick={() => handleSort('sales_executive_name')}>
              Sales Executive {getSortIcon('sales_executive_name')}
            </th>
            <th onClick={() => handleSort('source_type')}>
              Source Type {getSortIcon('source_type')}
            </th>
            <th onClick={() => handleSort('status')}>
              Status {getSortIcon('status')}
            </th>
            <th onClick={() => handleSort('date_of_sale')}>
              Date of Sale {getSortIcon('date_of_sale')}
            </th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {salesRecords.length > 0 ? (
            salesRecords.map((sale, index) => (
              <tr key={sale.id}>
                <td>{(page - 1) * limit + index + 1}</td>
                <td>{sale.client_name}</td>
                <td>{sale.client_id_no}</td>
                <td>{sale.client_phone}</td>
                <td>{sale.amount}</td>
                <td>{sale.policy_type_name}</td>
                <td>{sale.serial_number}</td>
                <td>{sale.sale_manager}</td>
                <td>{sale.sales_executive_name}</td>
                <td>{sale.source_type}</td>
                <td>{sale.status}</td>
                <td>{new Date(sale.date_of_sale).toLocaleDateString()}</td>
                <td>
                  <Button
                    variant="warning"
                    size="sm"
                    className="me-2"
                    onClick={() => handleEdit(sale)}
                  >
                    <FontAwesomeIcon icon={faEdit} />
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => handleDelete(sale.id)}
                  >
                    <FontAwesomeIcon icon={faTrash} />
                  </Button>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="13" className="text-center">
                No sales records available.
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

      {/* Modal for Viewing/Editing Sale */}
      <Modal show={showModal} onHide={() => setShowModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Edit Sale</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {/* Add your form for editing sale here */}
          <Form>
            <Form.Group controlId="editClientName">
              <Form.Label>Client Name</Form.Label>
              <Form.Control type="text" value={currentSale?.client_name || ''} readOnly />
            </Form.Group>
            {/* Add other fields here */}
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModal(false)}>
            Close
          </Button>
          <Button variant="primary" onClick={() => {/* Handle save logic here */}}>
            Save Changes
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default SalesTable;
