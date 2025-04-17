import React, { useEffect, useState } from 'react';
import { Card, Typography, Button, Modal, TextField, Grid, Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import { Container, Row, Col, Table, Spinner, Pagination } from 'react-bootstrap';
import api from '../services/api'; // Axios instance
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faEdit, faTrashAlt, faSitemap, faMapMarkerAlt, faPhone, faEnvelope, faGlobe } from '@fortawesome/free-solid-svg-icons';

const ManageBanksPage = ({ showToast }) => {
  const [banks, setBanks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showBankModal, setShowBankModal] = useState(false);
  const [showBranchModal, setShowBranchModal] = useState(false);
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [showDeleteBranchConfirmation, setShowDeleteBranchConfirmation] = useState(false);
  const [selectedBank, setSelectedBank] = useState(null);
  const [selectedBranch, setSelectedBranch] = useState(null);
  const [modalMode, setModalMode] = useState('add'); // 'add' or 'edit'
  const [bankData, setBankData] = useState({
    name: '',
    code: '',
    website: '',
    contact_email: '',
    contact_phone: '',
    logo_url: '',
    bank_type: ''
  });
  const [branchData, setBranchData] = useState({
    name: '',
    code: '',
    sort_code: '',
    address: '',
    city: '',
    region: '',
    country: '',
    latitude: '',
    longitude: '',
    contact_phone: '',
    contact_email: ''
  });
  const [branches, setBranches] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [bankTypeFilter, setBankTypeFilter] = useState('');
  const [cityFilter, setCityFilter] = useState('');

  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const banksPerPage = 10;

  // Fetch current logged-in user and role
  const local_user = JSON.parse(localStorage.getItem('user'));
  const role_id = parseInt(local_user?.role_id) || local_user?.role?.id;

  // Fetch all banks on component mount
  useEffect(() => {
    const fetchBanks = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams({
          page: currentPage,
          per_page: banksPerPage,
          ...(searchQuery && { search: searchQuery }),
          ...(bankTypeFilter && { bank_type: bankTypeFilter })
        });
        const response = await api.get(`/bank/?${params}`);
        setBanks(response.data);
      } catch (error) {
        console.error('Error fetching banks:', error);
        showToast('error', 'Failed to fetch banks. Please try again later.', 'Error');
      } finally {
        setLoading(false);
      }
    };
    fetchBanks();
  }, [currentPage, searchQuery, bankTypeFilter, showToast]);

  // Handle pagination
  const indexOfLastBank = currentPage * banksPerPage;
  const indexOfFirstBank = indexOfLastBank - banksPerPage;
  const currentBanks = banks.slice(indexOfFirstBank, indexOfLastBank);

  const paginate = (pageNumber) => setCurrentPage(pageNumber);

  // Handle opening and closing modals
  const handleOpenBankModal = (mode, bank = null) => {
    setModalMode(mode);
    if (mode === 'edit' && bank) {
      setSelectedBank(bank);
      setBankData({
        name: bank.name,
        code: bank.code || '',
        website: bank.website || '',
        contact_email: bank.contact_email || '',
        contact_phone: bank.contact_phone || '',
        logo_url: bank.logo_url || '',
        bank_type: bank.bank_type || ''
      });
    } else {
      setBankData({
        name: '',
        code: '',
        website: '',
        contact_email: '',
        contact_phone: '',
        logo_url: '',
        bank_type: ''
      });
    }
    setShowBankModal(true);
  };

  const handleCloseBankModal = () => {
    setShowBankModal(false);
    setSelectedBank(null);
  };

  const handleOpenBranchModal = (bank) => {
    setSelectedBank(bank);
    setBranches(bank.bank_branches || []);
    setShowBranchModal(true);
  };

  const handleCloseBranchModal = () => {
    setShowBranchModal(false);
    setBranchData({
      name: '',
      code: '',
      sort_code: '',
      address: '',
      city: '',
      region: '',
      country: '',
      latitude: '',
      longitude: '',
      contact_phone: '',
      contact_email: ''
    });
  };

  // Handle form submission for adding or editing a bank
  const handleSubmitBank = async () => {
    try {
      if (modalMode === 'add') {
        const response = await api.post('/bank/', bankData);
        setBanks((prevBanks) => [...prevBanks, response.data.bank]);
        showToast('success', 'Bank added successfully.', 'Success');
      } else if (modalMode === 'edit' && selectedBank) {
        const response = await api.put(`/bank/${selectedBank.id}`, bankData);
        setBanks((prevBanks) =>
          prevBanks.map((bank) => (bank.id === selectedBank.id ? response.data.bank : bank))
        );
        showToast('success', 'Bank updated successfully.', 'Success');
      }
      handleCloseBankModal();
    } catch (error) {
      console.error('Error saving bank:', error);
      showToast('error', 'Failed to save bank. Please try again later.', 'Error');
    }
  };

  // Handle form submission for adding or editing a branch
  const handleSubmitBranch = async () => {
    try {
      if (modalMode === 'add') {
        const response = await api.post('/bank/bank-branches/', {
          ...branchData,
          bank_id: selectedBank.id
        });
        setBranches((prevBranches) => [...prevBranches, response.data.branch]);
        showToast('success', 'Branch added successfully.', 'Success');
      } else if (modalMode === 'edit' && selectedBranch) {
        const response = await api.put(`/bank/bank-branches/${selectedBranch.id}`, branchData);
        setBranches((prevBranches) =>
          prevBranches.map((branch) => (branch.id === selectedBranch.id ? response.data.branch : branch))
        );
        showToast('success', 'Branch updated successfully.', 'Success');
      }
      handleCloseBranchModal();
    } catch (error) {
      console.error('Error saving branch:', error);
      showToast('error', 'Failed to save branch. Please try again later.', 'Error');
    }
  };

  // Handle deleting a bank
  const handleDeleteBank = async () => {
    if (!selectedBank) {
      showToast('error', 'No bank selected for deletion.', 'Error');
      return;
    }

    try {
      await api.delete(`/bank/${selectedBank.id}`);
      setBanks((prevBanks) => prevBanks.filter((bank) => bank.id !== selectedBank.id));
      showToast('success', 'Bank deleted successfully.', 'Success');
      setShowDeleteConfirmation(false);
      setSelectedBank(null);
    } catch (error) {
      console.error('Error deleting bank:', error);
      showToast('error', 'Failed to delete bank. Please try again later.', 'Error');
    }
  };

  // Handle deleting a branch
  const handleDeleteBranch = async () => {
    if (!selectedBranch) {
      showToast('error', 'No branch selected for deletion.', 'Error');
      return;
    }

    try {
      await api.delete(`/bank/bank-branches/${selectedBranch.id}`);
      setBranches((prevBranches) => prevBranches.filter((branch) => branch.id !== selectedBranch.id));
      showToast('success', 'Branch deleted successfully.', 'Success');
      setShowDeleteBranchConfirmation(false);
      setSelectedBranch(null);
    } catch (error) {
      console.error('Error deleting branch:', error);
      showToast('error', 'Failed to delete branch. Please try again later.', 'Error');
    }
  };

  // Bank modal content
  const renderBankModal = () => (
    <Modal open={showBankModal} onClose={handleCloseBankModal}>
      <Card sx={{ p: 3, maxWidth: 600, margin: 'auto', mt: 5 }}>
        <Typography variant="h5" gutterBottom>
          {modalMode === 'add' ? 'Add New Bank' : 'Edit Bank'}
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Bank Name"
              value={bankData.name}
              onChange={(e) => setBankData({ ...bankData, name: e.target.value })}
              required
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Bank Code"
              value={bankData.code}
              onChange={(e) => setBankData({ ...bankData, code: e.target.value })}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Bank Type</InputLabel>
              <Select
                value={bankData.bank_type}
                onChange={(e) => setBankData({ ...bankData, bank_type: e.target.value })}
                label="Bank Type"
              >
                <MenuItem value="Commercial">Commercial</MenuItem>
                <MenuItem value="Development">Development</MenuItem>
                <MenuItem value="Investment">Investment</MenuItem>
                <MenuItem value="Central">Central</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Website"
              value={bankData.website}
              onChange={(e) => setBankData({ ...bankData, website: e.target.value })}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Contact Email"
              value={bankData.contact_email}
              onChange={(e) => setBankData({ ...bankData, contact_email: e.target.value })}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Contact Phone"
              value={bankData.contact_phone}
              onChange={(e) => setBankData({ ...bankData, contact_phone: e.target.value })}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Logo URL"
              value={bankData.logo_url}
              onChange={(e) => setBankData({ ...bankData, logo_url: e.target.value })}
            />
          </Grid>
        </Grid>
        <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
          <Button variant="outlined" onClick={handleCloseBankModal}>
            Cancel
          </Button>
          <Button variant="contained" onClick={handleSubmitBank}>
            {modalMode === 'add' ? 'Add Bank' : 'Update Bank'}
          </Button>
        </div>
      </Card>
    </Modal>
  );

  // Branch modal content
  const renderBranchModal = () => (
    <Modal open={showBranchModal} onClose={handleCloseBranchModal}>
      <Card sx={{ p: 3, maxWidth: 600, margin: 'auto', mt: 5 }}>
        <Typography variant="h5" gutterBottom>
          {modalMode === 'add' ? 'Add New Branch' : 'Edit Branch'}
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Branch Name"
              value={branchData.name}
              onChange={(e) => setBranchData({ ...branchData, name: e.target.value })}
              required
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Branch Code"
              value={branchData.code}
              onChange={(e) => setBranchData({ ...branchData, code: e.target.value })}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Sort Code"
              value={branchData.sort_code}
              onChange={(e) => setBranchData({ ...branchData, sort_code: e.target.value })}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Address"
              value={branchData.address}
              onChange={(e) => setBranchData({ ...branchData, address: e.target.value })}
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              label="City"
              value={branchData.city}
              onChange={(e) => setBranchData({ ...branchData, city: e.target.value })}
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              label="Region"
              value={branchData.region}
              onChange={(e) => setBranchData({ ...branchData, region: e.target.value })}
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              label="Country"
              value={branchData.country}
              onChange={(e) => setBranchData({ ...branchData, country: e.target.value })}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Latitude"
              type="number"
              value={branchData.latitude}
              onChange={(e) => setBranchData({ ...branchData, latitude: e.target.value })}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Longitude"
              type="number"
              value={branchData.longitude}
              onChange={(e) => setBranchData({ ...branchData, longitude: e.target.value })}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Contact Phone"
              value={branchData.contact_phone}
              onChange={(e) => setBranchData({ ...branchData, contact_phone: e.target.value })}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Contact Email"
              value={branchData.contact_email}
              onChange={(e) => setBranchData({ ...branchData, contact_email: e.target.value })}
            />
          </Grid>
        </Grid>
        <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
          <Button variant="outlined" onClick={handleCloseBranchModal}>
            Cancel
          </Button>
          <Button variant="contained" onClick={handleSubmitBranch}>
            {modalMode === 'add' ? 'Add Branch' : 'Update Branch'}
          </Button>
        </div>
      </Card>
    </Modal>
  );

  return (
    <Container>
      <Row className="mb-4">
        <Col>
          <Typography variant="h4" gutterBottom>
            Manage Banks
          </Typography>
        </Col>
        <Col className="text-end">
          <Button
            variant="contained"
            startIcon={<FontAwesomeIcon icon={faPlus} />}
            onClick={() => handleOpenBankModal('add')}
          >
            Add Bank
          </Button>
        </Col>
      </Row>

      {/* Search and Filter Section */}
      <Row className="mb-4">
        <Col md={4}>
          <TextField
            fullWidth
            label="Search Banks"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </Col>
        <Col md={4}>
          <FormControl fullWidth>
            <InputLabel>Bank Type</InputLabel>
            <Select
              value={bankTypeFilter}
              onChange={(e) => setBankTypeFilter(e.target.value)}
              label="Bank Type"
            >
              <MenuItem value="">All Types</MenuItem>
              <MenuItem value="Commercial">Commercial</MenuItem>
              <MenuItem value="Development">Development</MenuItem>
              <MenuItem value="Investment">Investment</MenuItem>
              <MenuItem value="Central">Central</MenuItem>
            </Select>
          </FormControl>
        </Col>
      </Row>

      {loading ? (
        <div className="text-center">
          <Spinner animation="border" />
        </div>
      ) : (
        <>
          <Table striped bordered hover responsive>
            <thead>
              <tr>
                <th>Name</th>
                <th>Code</th>
                <th>Type</th>
                <th>Contact</th>
                <th>Branches</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {currentBanks.map((bank) => (
                <tr key={bank.id}>
                  <td>
                    {bank.logo_url && (
                      <img
                        src={bank.logo_url}
                        alt={bank.name}
                        style={{ width: 30, height: 30, marginRight: 10 }}
                      />
                    )}
                    {bank.name}
                  </td>
                  <td>{bank.code}</td>
                  <td>{bank.bank_type}</td>
                  <td>
                    <div>
                      {bank.contact_phone && (
                        <div>
                          <FontAwesomeIcon icon={faPhone} /> {bank.contact_phone}
                        </div>
                      )}
                      {bank.contact_email && (
                        <div>
                          <FontAwesomeIcon icon={faEnvelope} /> {bank.contact_email}
                        </div>
                      )}
                      {bank.website && (
                        <div>
                          <FontAwesomeIcon icon={faGlobe} />{' '}
                          <a href={bank.website} target="_blank" rel="noopener noreferrer">
                            Website
                          </a>
                        </div>
                      )}
                    </div>
                  </td>
                  <td>
                    <Button
                      variant="outlined"
                      startIcon={<FontAwesomeIcon icon={faSitemap} />}
                      onClick={() => handleOpenBranchModal(bank)}
                    >
                      {bank.bank_branches?.length || 0} Branches
                    </Button>
                  </td>
                  <td>
                    <Button
                      variant="outlined"
                      startIcon={<FontAwesomeIcon icon={faEdit} />}
                      onClick={() => handleOpenBankModal('edit', bank)}
                      style={{ marginRight: 10 }}
                    >
                      Edit
                    </Button>
                    <Button
                      variant="outlined"
                      color="error"
                      startIcon={<FontAwesomeIcon icon={faTrashAlt} />}
                      onClick={() => {
                        setSelectedBank(bank);
                        setShowDeleteConfirmation(true);
                      }}
                    >
                      Delete
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>

          <Pagination className="justify-content-center">
            {Array.from({ length: Math.ceil(banks.length / banksPerPage) }).map((_, index) => (
              <Pagination.Item
                key={index + 1}
                active={index + 1 === currentPage}
                onClick={() => paginate(index + 1)}
              >
                {index + 1}
              </Pagination.Item>
            ))}
          </Pagination>
        </>
      )}

      {renderBankModal()}
      {renderBranchModal()}

      {/* Delete Confirmation Modal */}
      <Modal open={showDeleteConfirmation} onClose={() => setShowDeleteConfirmation(false)}>
        <Card sx={{ p: 3, maxWidth: 400, margin: 'auto', mt: 5 }}>
          <Typography variant="h6" gutterBottom>
            Confirm Delete
          </Typography>
          <Typography>
            Are you sure you want to delete {selectedBank?.name}? This action cannot be undone.
          </Typography>
          <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <Button variant="outlined" onClick={() => setShowDeleteConfirmation(false)}>
              Cancel
            </Button>
            <Button variant="contained" color="error" onClick={handleDeleteBank}>
              Delete
            </Button>
          </div>
        </Card>
      </Modal>

      {/* Branch Delete Confirmation Modal */}
      <Modal open={showDeleteBranchConfirmation} onClose={() => setShowDeleteBranchConfirmation(false)}>
        <Card sx={{ p: 3, maxWidth: 400, margin: 'auto', mt: 5 }}>
          <Typography variant="h6" gutterBottom>
            Confirm Delete
          </Typography>
          <Typography>
            Are you sure you want to delete {selectedBranch?.name}? This action cannot be undone.
          </Typography>
          <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <Button variant="outlined" onClick={() => setShowDeleteBranchConfirmation(false)}>
              Cancel
            </Button>
            <Button variant="contained" color="error" onClick={handleDeleteBranch}>
              Delete
            </Button>
          </div>
        </Card>
      </Modal>
    </Container>
  );
};

export default ManageBanksPage;
