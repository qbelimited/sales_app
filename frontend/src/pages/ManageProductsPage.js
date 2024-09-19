import React, { useEffect, useState } from 'react';
import { Card, Typography, Button, Modal, TextField, MenuItem, Select, InputLabel, FormControl } from '@mui/material';
import { Container, Row, Col, Table, Spinner, Pagination } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faEdit, faTrashAlt } from '@fortawesome/free-solid-svg-icons';
import api from '../services/api'; // Axios instance

const ManageProductsPage = ({ showToast }) => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showProductModal, setShowProductModal] = useState(false);
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [modalMode, setModalMode] = useState('add'); // 'add' or 'edit'
  const [productData, setProductData] = useState({ name: '', category: '', group: '' });

  // Define allowed groups and categories
  const allowedGroups = ['risk', 'investment', 'hybrid'];
  const categories = ['Retail', 'Corporate', 'Micro'];

  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const productsPerPage = 10;

  // Fetch all products on component mount and on pagination change
  useEffect(() => {
    const fetchProducts = async () => {
      setLoading(true);
      try {
        const response = await api.get(`/impact_products/?sort_by=created_at&per_page=${productsPerPage}&page=${currentPage}`);
        setProducts(response.data.products);
        setTotalPages(Math.ceil(response.data.total / productsPerPage)); // Update total pages
      } catch (error) {
        console.error('Error fetching products:', error);
        showToast('error', 'Failed to fetch products. Please try again later.', 'Error');
      } finally {
        setLoading(false);
      }
    };
    fetchProducts();
  }, [showToast, currentPage]);

  // Handle pagination
  const paginate = (pageNumber) => setCurrentPage(pageNumber);

  // Handle opening and closing modals
  const handleOpenProductModal = (mode, product = null) => {
    setModalMode(mode);
    if (mode === 'edit' && product) {
      setSelectedProduct(product);
      setProductData({ name: product.name, category: product.category.name, group: product.group });
    } else {
      setProductData({ name: '', category: '', group: '' });
    }
    setShowProductModal(true);
  };

  const handleCloseProductModal = () => {
    setShowProductModal(false);
    setSelectedProduct(null);
  };

  // Handle form submission for adding or editing a product
  const handleSubmitProduct = async () => {
    try {
      if (modalMode === 'add') {
        const response = await api.post('/impact_products/', productData); // Add new product
        setProducts((prevProducts) => [...prevProducts, response.data]);
        showToast('success', 'Product added successfully.', 'Success');
      } else if (modalMode === 'edit' && selectedProduct) {
        const response = await api.put(`/impact_products/${selectedProduct.id}`, productData); // Edit product
        setProducts((prevProducts) =>
          prevProducts.map((product) => (product.id === selectedProduct.id ? response.data : product))
        );
        showToast('success', 'Product updated successfully.', 'Success');
      }
      handleCloseProductModal();
    } catch (error) {
      console.error('Error saving product:', error);
      showToast('error', 'Failed to save product. Please try again later.', 'Error');
    }
  };

  // Handle deleting a product
  const handleDeleteProduct = async () => {
    if (!selectedProduct) {
      showToast('error', 'No product selected for deletion.', 'Error');
      return;
    }

    try {
      await api.delete(`/impact_products/${selectedProduct.id}`); // Delete product
      setProducts((prevProducts) => prevProducts.filter((product) => product.id !== selectedProduct.id));
      showToast('success', 'Product deleted successfully.', 'Success');
      setShowDeleteConfirmation(false);
      setSelectedProduct(null);
    } catch (error) {
      console.error('Error deleting product:', error);
      showToast('error', 'Failed to delete product. Please try again later.', 'Error');
    }
  };

  // Handle opening delete confirmation modal
  const handleShowDeleteConfirmation = (product) => {
    if (!product) return;
    setSelectedProduct(product);
    setShowDeleteConfirmation(true);
  };

  if (loading) return <Spinner animation="border" />;

  return (
    <Container className="mt-4">
      <Row>
        <Col md={12}>
          <Typography variant="h4" gutterBottom>
            Product Management
          </Typography>
        </Col>
      </Row>
      <Row>
        <Col md={12}>
          <Button
            variant="contained"
            color="primary"
            onClick={() => handleOpenProductModal('add')}
          >
            <FontAwesomeIcon icon={faPlus} /> Add New Product
          </Button>
        </Col>
      </Row>

      <Row className="mt-4">
        <Col md={12}>
          <Table striped bordered hover>
            <thead>
              <tr>
                <th>Name</th>
                <th>Category</th>
                <th>Group</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => (
                <tr key={product.id}>
                  <td>{product.name}</td>
                  <td>{product.category.name}</td>
                  <td>{product.group}</td>
                  <td>
                    <Button
                      variant="contained"
                      color="secondary"
                      onClick={() => handleOpenProductModal('edit', product)}
                      className="me-2"
                    >
                      <FontAwesomeIcon icon={faEdit} /> Edit
                    </Button>
                    <Button
                      variant="contained"
                      color="error"
                      onClick={() => handleShowDeleteConfirmation(product)}
                    >
                      <FontAwesomeIcon icon={faTrashAlt} /> Delete
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
          {/* Pagination */}
          <Pagination>
            {Array.from({ length: totalPages }, (_, index) => (
              <Pagination.Item key={index + 1} active={index + 1 === currentPage} onClick={() => paginate(index + 1)}>
                {index + 1}
              </Pagination.Item>
            ))}
          </Pagination>
        </Col>
      </Row>

      {/* Modal for Add/Edit Product */}
      <Modal
        open={showProductModal}
        onClose={handleCloseProductModal}
        style={{ overflow: 'auto' }}
      >
        <Card style={{ width: '50%', margin: '5% auto', padding: '20px', maxHeight: '80vh', overflowY: 'auto' }}>
          <Typography variant="h5" gutterBottom>
            {modalMode === 'add' ? 'Add New Product' : 'Edit Product'}
          </Typography>
          <TextField
            fullWidth
            label="Product Name"
            value={productData.name}
            onChange={(e) => setProductData({ ...productData, name: e.target.value })}
            margin="normal"
          />
          <FormControl fullWidth margin="normal">
            <InputLabel>Category</InputLabel>
            <Select
              value={productData.category}
              onChange={(e) => setProductData({ ...productData, category: e.target.value })}
            >
              {categories.map((category) => (
                <MenuItem key={category} value={category}>{category}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth margin="normal">
            <InputLabel>Group</InputLabel>
            <Select
              value={productData.group}
              onChange={(e) => setProductData({ ...productData, group: e.target.value })}
            >
              {allowedGroups.map((group) => (
                <MenuItem key={group} value={group}>{group}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <Row className="mt-3">
            <Col md={6}>
              <Button variant="contained" color="primary" onClick={handleSubmitProduct}>
                Save
              </Button>
            </Col>
            <Col md={6}>
              <Button variant="outlined" color="secondary" onClick={handleCloseProductModal}>
                Cancel
              </Button>
            </Col>
          </Row>
        </Card>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        open={showDeleteConfirmation}
        onClose={() => setShowDeleteConfirmation(false)}
        style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}
      >
        <Card style={{ padding: '20px' }}>
          <Typography variant="h6" gutterBottom>
            Are you sure you want to delete this product?
          </Typography>
          <Row className="mt-3">
            <Col md={6}>
              <Button variant="contained" color="error" onClick={handleDeleteProduct}>
                Delete
              </Button>
            </Col>
            <Col md={6}>
              <Button variant="outlined" color="secondary" onClick={() => setShowDeleteConfirmation(false)}>
                Cancel
              </Button>
            </Col>
          </Row>
        </Card>
      </Modal>
    </Container>
  );
};

export default ManageProductsPage;
