import React, { useState, useEffect, useCallback } from 'react';
import { Table, Button, Pagination, Spinner, Form, Row, Col, Modal, Badge } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEdit, faTrash, faSort, faSortUp, faSortDown, faEye } from '@fortawesome/free-solid-svg-icons';
import api from '../services/api';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import SalesForm from '../components/SalesForm';
import SalesEditForm from '../components/SalesEditForm';
import { useNavigate } from 'react-router-dom';

const SalesPage = ({ showToast }) => {
  const [salesRecords, setSalesRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortConfig, setSortConfig] = useState({ key: 'created_at', direction: 'desc' });
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({ startDate: null, endDate: null, clientName: '', bankId: '', productId: '', status: '' });
  const [showModal, setShowModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [currentSale, setCurrentSale] = useState(null);
  const [banks, setBanks] = useState([]);
  const [products, setProducts] = useState([]);
  const [salesExecutives, setSalesExecutives] = useState([]);
  const [saleToDelete, setSaleToDelete] = useState(null);

  const local_user = JSON.parse(localStorage.getItem('user'));
  const loggedInUserName = local_user?.name;
  const role = local_user?.role?.name;
  const navigate = useNavigate();

  const maxPageDisplay = 5;

  const handleViewDetails = (saleId) => {
    navigate(`/sales/${saleId}`);
  };

  const fetchBanksAndProducts = useCallback(async () => {
    try {
      const bankResponse = await api.get('/bank/');
      setBanks(bankResponse.data);

      const productResponse = await api.get('/impact_products/?sort_by=created_at&per_page=100&page=1');
      setProducts(productResponse.data.products);
    } catch (error) {
      console.error('Error fetching banks/products:', error);
      showToast('danger', 'Failed to fetch banks/products.', 'Error');
    }
  }, [showToast]);

  const fetchSalesExecutives = useCallback(async () => {
    try {
      const restot = await api.get('/sales_executives/', {
        params: {
          sort_by: 'created_at',
          per_page: 10,
          page: 1,
        },
      });
      const total = parseInt(restot.data.total);

      const response = await api.get('/sales_executives/', {
        params: {
          sort_by: 'created_at',
          per_page: total,
          page: 1,
        },
      });
      setSalesExecutives(Array.isArray(response.data.sales_executives) ? response.data.sales_executives : []);
    } catch (error) {
      console.error('Error fetching sales executives:', error);
      showToast('danger', 'Failed to fetch sales executives.', 'Error');
      setSalesExecutives([]);
    }
  }, [showToast]);

  const fetchSalesRecords = useCallback(async (currentPage, sortKey, sortDirection, filterParams) => {
    setLoading(true);
    try {
      const res1tot = await api.get('/sales/', { params: { sort_by: 'created_at', per_page: 10, page: 1 } });
      const total1 = parseInt(res1tot.data.total);

      const params = {
        page: currentPage,
        per_page: total1,
        ...filterParams,
      };

      if (filterParams.startDate) {
        params.startDate = filterParams.startDate.toISOString().split('T')[0];
      }
      if (filterParams.endDate) {
        params.endDate = filterParams.endDate.toISOString().split('T')[0];
      }

      const response = await api.get('/sales/', { params });
      let salesData = response.data.sales || [];

      // Filter based on start and end date
      if (filterParams.startDate || filterParams.endDate) {
        salesData = salesData.filter(sale => {
          const createdAt = new Date(sale.created_at);
          const isAfterStartDate = filterParams.startDate ? createdAt >= filterParams.startDate : true;
          const isBeforeEndDate = filterParams.endDate ? createdAt <= filterParams.endDate : true;
          return isAfterStartDate && isBeforeEndDate;
        });
      }

      // New filtering logic for client, sales manager, and sales executive names
      if (filterParams.clientName) {
        salesData = salesData.filter(sale => {
          const clientNameMatch = sale.client_name?.toLowerCase().includes(filterParams.clientName.toLowerCase());
          const managerNameMatch = sale.sale_manager?.name?.toLowerCase().includes(filterParams.clientName.toLowerCase());
          const executiveNameMatch = salesExecutives.find(executive => executive.id === sale.sales_executive_id)?.name?.toLowerCase().includes(filterParams.clientName.toLowerCase());

          return clientNameMatch || managerNameMatch || executiveNameMatch;
        });
      }

      // Filtering by product
      if (filterParams.productId) {
        salesData = salesData.filter(sale => sale.product_id === filterParams.productId);
      }

      const sortedSales = sortSalesData(salesData, sortKey, sortDirection);

      const filteredSales = sortedSales.filter(
        (sale) => (sale.sale_manager?.name || '').toLowerCase() === (loggedInUserName || '').toLowerCase()
      );

      if (role === 'Sales_Manager') {
        setSalesRecords(filteredSales.length > 0 ? filteredSales : []);
      } else {
        setSalesRecords(sortedSales);
      }

      setTotalPages(response.data.pages || 1);
    } catch (error) {
      console.error('Error fetching sales records:', error);
      showToast('danger', 'Failed to fetch sales records.', 'Error');
    } finally {
      setLoading(false);
    }
  }, [showToast, loggedInUserName, role, salesExecutives]);

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
    fetchSalesRecords(1, key, direction, filters);
  };

  const handlePageChange = (pageNumber) => {
    if (pageNumber >= 1 && pageNumber <= totalPages) {
      setPage(pageNumber);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((prevFilters) => ({ ...prevFilters, [name]: value }));
  };

  const handleFilterSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchSalesRecords(1, sortConfig.key, sortConfig.direction, filters);
  };

  const handleResetFilters = () => {
    setFilters({ startDate: null, endDate: null, clientName: '', bankId: '', productId: '', status: '' });
    fetchSalesRecords(1, sortConfig.key, sortConfig.direction, {
      startDate: null, endDate: null, clientName: '', bankId: '', productId: '', status: ''
    });
  };

  const handleEdit = (sale) => {
    setCurrentSale(sale);
    setShowModal(true);
  };

  const confirmDelete = (sale) => {
    setSaleToDelete(sale);
    setShowDeleteModal(true);
  };

  const sortSalesData = (salesData, sortKey, sortDirection) => {
    return salesData.sort((a, b) => {
      let aValue, bValue;

      if (sortKey === 'policy_type') {
        aValue = a.policy_type?.name || '';
        bValue = b.policy_type?.name || '';
      } else if (sortKey === 'sales_manager') {
        aValue = a.sale_manager?.name || '';
        bValue = b.sale_manager?.name || '';
      } else {
        aValue = a[sortKey];
        bValue = b[sortKey];
      }

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  };

  const handleDelete = async () => {
    if (saleToDelete) {
      try {
        await api.delete(`/sales/${saleToDelete.id}`);
        setSalesRecords(salesRecords.filter((sale) => sale.id !== saleToDelete.id));
        showToast('success', 'Sale deleted successfully.', 'Success');
      } catch (error) {
        console.error('Error deleting sale:', error);
        showToast('danger', 'Failed to delete sale.', 'Error');
      } finally {
        setShowDeleteModal(false);
        setSaleToDelete(null);
        fetchSalesRecords(page, sortConfig.key, sortConfig.direction, filters);
      }
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
        showToast('success', 'Sale updated successfully.', 'Success');
      } catch (error) {
        console.error('Error updating sale record:', error);
        showToast('danger', 'Failed to update sale.', 'Error');
      }
    } else {
      try {
        const response = await api.post('/sales/', newSaleData);
        setSalesRecords([...salesRecords, response.data]);
        showToast('success', 'Sale added successfully.', 'Success');
      } catch (error) {
        console.error('Error adding new sale record:', error);
      }
    }

    setShowModal(false);
    setCurrentSale(null);
    fetchSalesRecords(page, sortConfig.key, sortConfig.direction, filters);
  };

  const renderStatusBadge = (status) => {
    let variant = 'secondary';
    if (status === 'submitted') {
      variant = 'success';
    } else if (status === 'under investigation') {
      variant = 'warning';
    } else if (status === 'rejected') {
      variant = 'danger';
    }
    return <Badge bg={variant} className="text-white">{status}</Badge>;
  };

  useEffect(() => {
    fetchSalesRecords(page, sortConfig.key, sortConfig.direction, filters);
  }, [page, sortConfig, filters, fetchSalesRecords]);

  useEffect(() => {
    fetchBanksAndProducts();
    fetchSalesExecutives();
  }, [fetchBanksAndProducts, fetchSalesExecutives]);

  const renderActions = (sale) => {
    const local_user = JSON.parse(localStorage.getItem('user'));
    const role_id = parseInt(local_user.role_id) || local_user.role.id;

    return (
      <>
        <Button
          variant="primary"
          size="sm"
          className="me-2"
          onClick={() => handleViewDetails(sale.id)}
        >
          <FontAwesomeIcon icon={faEye} />
        </Button>
        {role_id === 3 || role_id === 2 ? (
          <>
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
              onClick={() => confirmDelete(sale)}
            >
              <FontAwesomeIcon icon={faTrash} />
            </Button>
          </>
        ) : null}
      </>
    );
  };

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

  const handleFilterByStatus = (status) => {
    setFilters((prev) => ({ ...prev, status }));
    fetchSalesRecords(1, sortConfig.key, sortConfig.direction, { ...filters, status });
  };

  if (loading) {
    return (
      <div className="text-center mt-5">
        <Spinner animation="border" />
      </div>
    );
  }

  if (role === 'Sales_Manager' && salesRecords.length === 0) {
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
        <h3 className="text-center text-muted">No sales keyed by manager yet</h3>

        <Modal show={showModal} onHide={() => setShowModal(false)} size="lg">
          <Modal.Header closeButton>
            <Modal.Title>{currentSale ? 'Edit Sale' : 'Add New Sale'}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            {currentSale ? (
              <SalesEditForm
                saleData={currentSale}
                onCancel={() => setShowModal(false)}
                onSubmit={handleFormSubmit}
              />
            ) : (
              <SalesForm
                onSubmit={handleFormSubmit}
                onCancel={() => setShowModal(false)}
              />
            )}
          </Modal.Body>
        </Modal>
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

      <Row className="mb-3">
        <Col>
          <Button variant="info" onClick={() => handleFilterByStatus('submitted')}>
            Filter Submitted
          </Button>
          <Button variant="warning" onClick={() => handleFilterByStatus('under investigation')}>
            Filter Under Investigation
          </Button>
          <Button variant="danger" onClick={() => handleFilterByStatus('rejected')}>
            Filter Rejected
          </Button>
          <Button variant="secondary" onClick={handleResetFilters}>
            Reset Filters
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
              <Form.Label>Name filter</Form.Label>
              <Form.Control
                type="text"
                name="clientName"
                value={filters.clientName}
                onChange={handleFilterChange}
                placeholder="Enter name"
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
            <Form.Group controlId="filterProduct">
              <Form.Label>Product</Form.Label>
              <Form.Control as="select" name="productId" value={filters.productId} onChange={handleFilterChange}>
                <option value="">Select Product</option>
                {products.map((product) => (
                  <option key={product.id} value={product.id}>
                    {product.name}
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
            <th onClick={() => handleSort('sales_manager')}>
              Sales Manager {getSortIcon('sales_manager')}
            </th>
            <th onClick={() => handleSort('sales_executive_id')}>
              Sales Executive {getSortIcon('sales_executive_id')}
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
                <td>{(page - 1) * 10 + index + 1}</td>
                <td>{sale.client_name}</td>
                <td>{sale.amount}</td>
                <td>{sale.policy_type?.name || 'N/A'}</td>
                <td>{sale.serial_number}</td>
                <td>{sale.sale_manager?.name || 'N/A'}</td>
                <td>
                  {
                    salesExecutives.find(executive => executive.id === sale.sales_executive_id)?.name || sale.sales_executive_id
                  }
                </td>
                <td>{sale.source_type}</td>
                <td>{renderStatusBadge(sale.status)}</td>
                <td>{new Date(sale.created_at).toLocaleDateString()}</td>
                <td>{renderActions(sale)}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="11" className="text-center">
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

      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Deletion</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Are you sure you want to delete this sale record?
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>Cancel</Button>
          <Button variant="danger" onClick={handleDelete}>
            Delete
          </Button>
        </Modal.Footer>
      </Modal>

      <Modal show={showModal} onHide={() => setShowModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>{currentSale ? 'Edit Sale' : 'Add New Sale'}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {currentSale ? (
            <SalesEditForm
              saleData={currentSale}
              onCancel={() => setShowModal(false)}
              onSubmit={handleFormSubmit}
            />
          ) : (
            <SalesForm
              onSubmit={handleFormSubmit}
              onCancel={() => setShowModal(false)}
            />
          )}
        </Modal.Body>
      </Modal>
    </div>
  );
};

export default SalesPage;
