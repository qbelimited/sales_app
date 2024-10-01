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
  const [filters, setFilters] = useState({ startDate: null, endDate: null, clientName: '', bankId: '', branchId: '' });
  const [showModal, setShowModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [currentSale, setCurrentSale] = useState(null);
  const [banks, setBanks] = useState([]);
  const [branches, setBranches] = useState([]);
  const [salesExecutives, setSalesExecutives] = useState([]);
  const [saleToDelete, setSaleToDelete] = useState(null); // Track sale to delete

  const local_user = JSON.parse(localStorage.getItem('user')); // Fetch current logged-in user
  const loggedInUserName = local_user?.name; // Get logged-in user's name
  const role = local_user?.role?.name; // Get logged-in user's role
  const navigate = useNavigate();

  // Maximum number of pages to display
  const maxPageDisplay = 5;

  // Function to navigate to the details page
  const handleViewDetails = (saleId) => {
    navigate(`/sales/${saleId}`);
  };

  // Fetch banks and branches data
  const fetchBanksAndBranches = useCallback(async () => {
    try {
      const response = await api.get('/bank/');
      setBanks(response.data);
    } catch (error) {
      console.error('Error fetching banks:', error);
      showToast('danger', 'Failed to fetch banks.', 'Error');
    }
  }, [showToast]);

  const fetchBranches = async (bankId) => {
    try {
      if (bankId) {
        const response = await api.get('/dropdown/', {
          params: { type: 'branch', bank_id: bankId },
        });
        setBranches(response.data);
      } else {
        setBranches([]);
      }
    } catch (error) {
      console.error('Error fetching branches:', error);
      showToast('danger', 'Failed to fetch branches.', 'Error');
    }
  };

  // Fetch sales executives
  const fetchSalesExecutives = useCallback(async () => {
    try {
      // Get the total sales executives
      const restot = await api.get('/sales_executives/', {
        params: {
          sort_by: 'created_at',
          per_page: 10,
          page: 1,
        },
      });
      const total = parseInt(restot.data.total);

      // Get all sales executives
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

  // Fetch sales records and filter based on sales manager (logged-in user)
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

      // Format dates for API request
      if (filterParams.startDate) {
        params.startDate = filterParams.startDate.toISOString().split('T')[0];
      }
      if (filterParams.endDate) {
        params.endDate = filterParams.endDate.toISOString().split('T')[0];
      }

      const response = await api.get('/sales/', { params });
      let salesData = response.data.sales || [];

      // Sort and filter sales data
      const sortedSales = sortSalesData(salesData, sortKey, sortDirection);
      const filteredSales = sortedSales.filter(
        (sale) => (sale.sale_manager?.name || '').toLowerCase() === (loggedInUserName || '').toLowerCase()
      );

      // Update sales records and total pages based on filtered results
      setSalesRecords(filteredSales);
      setTotalPages(Math.ceil(filteredSales.length / 10)); // Set total pages based on filtered sales count
    } catch (error) {
      console.error('Error fetching sales records:', error);
      showToast('danger', 'Failed to fetch sales records.', 'Error');
    } finally {
      setLoading(false);
    }
  }, [showToast, loggedInUserName]);

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
    fetchSalesRecords(1, key, direction, filters); // Fetch new records with the updated sorting
    setPage(1); // Reset to first page on sort change
  };

  const handlePageChange = (pageNumber) => {
    if (pageNumber >= 1 && pageNumber <= totalPages) {
      setPage(pageNumber);
      fetchSalesRecords(pageNumber, sortConfig.key, sortConfig.direction, filters); // Fetch records for the new page
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((prevFilters) => ({ ...prevFilters, [name]: value }));
    if (name === 'bankId') {
      fetchBranches(value);
    }
  };

  const handleFilterSubmit = (e) => {
    e.preventDefault();
    setPage(1); // Reset to the first page when filters are applied
    fetchSalesRecords(1, sortConfig.key, sortConfig.direction, filters); // Fetch filtered records
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

      // Determine the value to sort by
      if (sortKey === 'policy_type') {
        aValue = a.policy_type?.name || ''; // Fallback to empty string if undefined
        bValue = b.policy_type?.name || ''; // Fallback to empty string if undefined
      } else if (sortKey === 'sales_manager') {
        aValue = a.sale_manager?.name || ''; // Fallback to empty string if undefined
        bValue = b.sale_manager?.name || ''; // Fallback to empty string if undefined
      } else {
        aValue = a[sortKey];
        bValue = b[sortKey];
      }

      // Compare values based on sort direction
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
        fetchSalesRecords(page, sortConfig.key, sortConfig.direction, filters); // Re-fetch records to ensure table is up to date
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
    fetchSalesRecords(page, sortConfig.key, sortConfig.direction, filters); // Re-fetch records to ensure table is up to date
  };

  // Render the status with color coding
  const renderStatusBadge = (status) => {
    let variant = 'secondary'; // Default color
    if (status === 'submitted') {
      variant = 'success'; // Green for submitted
    } else if (status === 'under investigation') {
      variant = 'warning'; // Yellow for under investigation
    } else if (status === 'rejected') {
      variant = 'danger'; // Red for rejected
    }
    return <Badge bg={variant} className="text-white">{status}</Badge>;
  };

  useEffect(() => {
    fetchSalesRecords(page, sortConfig.key, sortConfig.direction, filters);
  }, [page, sortConfig, filters, fetchSalesRecords]);

  useEffect(() => {
    fetchBanksAndBranches();
    fetchSalesExecutives();
  }, [fetchBanksAndBranches, fetchSalesExecutives]);

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
        {role_id === 3 || role_id === 2 ? ( // Check if user is admin or manager
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

  if (loading) {
    return (
      <div className="text-center mt-5">
        <Spinner animation="border" />
      </div>
    );
  }

  // Render "No sales keyed by manager yet" if the user is Sales_Manager and no sales found
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

      {/* Delete Confirmation Modal */}
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

      {/* Sales Modal for Create/Edit */}
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
