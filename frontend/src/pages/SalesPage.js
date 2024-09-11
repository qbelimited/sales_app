import React, { useState, useEffect, useCallback } from 'react';
import { Table, Button, Pagination, Spinner, Form, Row, Col, Modal } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEdit, faTrash, faSort, faSortUp, faSortDown } from '@fortawesome/free-solid-svg-icons';
import api from '../services/api';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import SalesForm from '../components/SalesForm';

const SalesPage = () => {
  const [salesRecords, setSalesRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortConfig, setSortConfig] = useState({ key: 'client_name', direction: 'asc' });
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({ startDate: null, endDate: null, clientName: '', bankId: '', branchId: '' });
  const [showModal, setShowModal] = useState(false);
  const [currentSale, setCurrentSale] = useState(null);
  const [banks, setBanks] = useState([]);
  const [branches, setBranches] = useState([]);

  const limit = 10;
  const maxPageDisplay = 5;

  // Fetch banks and branches data
  const fetchBanks = async () => {
    try {
      const response = await api.get('/banks/'); // Assuming you have an endpoint for fetching banks
      setBanks(response.data);
    } catch (error) {
      console.error('Error fetching banks:', error);
    }
  };

  const fetchBranches = async (bankId) => {
    try {
      const response = await api.get(`/banks/${bankId}/branches`); // Assuming you have an endpoint for fetching branches by bank
      setBranches(response.data);
    } catch (error) {
      console.error('Error fetching branches:', error);
    }
  };

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

      const response = await api.get('/sales/', { params });
      setSalesRecords(response.data.sales || []);
      setTotalPages(response.data.pages || 1);
    } catch (error) {
      console.error('Error fetching sales records:', error);
    } finally {
      setLoading(false);
    }
  }, [limit]);

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
    if (name === 'bankId') {
      fetchBranches(value); // Load branches when a bank is selected
    }
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

  const handleFormSubmit = async (newSaleData) => {
    if (currentSale) {
      try {
        const response = await api.put(`/sales/${currentSale.id}`, newSaleData);
        setSalesRecords(
          salesRecords.map((sale) =>
            sale.id === currentSale.id ? { ...sale, ...response.data } : sale
          )
        );
      } catch (error) {
        console.error('Error updating sale record:', error);
      }
    } else {
      try {
        const response = await api.post('/sales/', newSaleData);
        setSalesRecords([...salesRecords, response.data]);
      } catch (error) {
        console.error('Error adding new sale record:', error);
      }
    }

    setShowModal(false);
    setCurrentSale(null);
  };

  useEffect(() => {
    fetchSalesRecords(page, sortConfig.key, sortConfig.direction, filters);
    fetchBanks(); // Load banks on component mount
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

  if (loading) {
    return (
      <div className="text-center mt-5">
        <Spinner animation="border" />
      </div>
    );
  }

  return (
    <div className="container mt-5">
      <Row className="mb-3">
        <Col>
          <h2 className="text-left">Sales Records</h2>
        </Col>
        <Col className="text-right">
          <Button onClick={() => setShowModal(true)} variant="primary" className="mb-3">
            Make Sale
          </Button>
        </Col>
      </Row>

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
          <Col>
            <Form.Group controlId="filterBank">
              <Form.Label>Bank</Form.Label>
              <Form.Control as="select" name="bankId" value={filters.bankId} onChange={handleFilterChange}>
                <option value="">Select Bank</option>
                {banks.map((bank) => (
                  <option key={bank.id} value={bank.id}>
                    {bank.name}
                  </option>
                ))}
              </Form.Control>
            </Form.Group>
          </Col>
          <Col>
            <Form.Group controlId="filterBranch">
              <Form.Label>Branch</Form.Label>
              <Form.Control as="select" name="branchId" value={filters.branchId} onChange={handleFilterChange}>
                <option value="">Select Branch</option>
                {branches.map((branch) => (
                  <option key={branch.id} value={branch.id}>
                    {branch.name}
                  </option>
                ))}
              </Form.Control>
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
            <th onClick={() => handleSort('amount')}>
              Amount {getSortIcon('amount')}
            </th>
            <th onClick={() => handleSort('policy_type')}>
              Policy Type {getSortIcon('policy_type')}
            </th>
            <th onClick={() => handleSort('serial_number')}>
              Serial Number {getSortIcon('serial_number')}
            </th>
            <th onClick={() => handleSort('sales_executive')}>
              Sales Executive {getSortIcon('sales_executive')}
            </th>
            <th onClick={() => handleSort('source_type')}>
              Source Type {getSortIcon('source_type')}
            </th>
            <th onClick={() => handleSort('status')}>
              Status {getSortIcon('status')}
            </th>
            <th onClick={() => handleSort('created_at')}>
              Date {getSortIcon('created_at')}
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
                <td>{sale.amount}</td>
                <td>{sale.policy_type.name}</td>
                <td>{sale.serial_number}</td>
                <td>{sale.sales_executive.name}</td>
                <td>{sale.source_type}</td>
                <td>{sale.status}</td>
                <td>{new Date(sale.created_at).toLocaleDateString()}</td>
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
              <td colSpan="10" className="text-center">
                No sales records available.
              </td>
            </tr>
          )}
        </tbody>
      </Table>

      <Pagination className="justify-content-center mt-4">
        <Pagination.First onClick={() => handlePageChange(1)} disabled={page === 1} />
        <Pagination.Prev onClick={() => handlePageChange(page - 1)} disabled={page === 1} />
        {renderPaginationItems()}
        <Pagination.Next onClick={() => handlePageChange(page + 1)} disabled={page === totalPages} />
        <Pagination.Last onClick={() => handlePageChange(totalPages)} disabled={page === totalPages} />
      </Pagination>

      <Modal show={showModal} onHide={() => setShowModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>{currentSale ? 'Edit Sale' : 'Add New Sale'}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <SalesForm
            onSubmit={handleFormSubmit}
            saleData={currentSale}
            onCancel={() => setShowModal(false)}
          />
        </Modal.Body>
      </Modal>
    </div>
  );
};

export default SalesPage;
