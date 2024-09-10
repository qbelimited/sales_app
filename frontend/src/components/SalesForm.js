import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';

const SalesForm = ({ saleData, onSubmit }) => {
  const [formData, setFormData] = useState({
    sale_manager_id: '',
    sales_executive_id: '',
    client_name: '',
    client_id_no: '',
    client_phone: '',
    serial_number: '',
    collection_platform: '',  // Default collection platform
    source_type: '',  // Default first payment type
    momo_reference_number: '',
    momo_transaction_id: '',
    first_pay_with_momo: false,  // Checkbox for first payment with Momo
    subsequent_pay_source_type: '',  // Subsequent payment method (paypoint or bank)
    bank_id: '',
    bank_branch_id: '',
    bank_acc_number: '',
    paypoint_name: '',
    paypoint_branch: '',
    staff_id: '',
    policy_type_id: '',
    amount: '',
    customer_called: false,  // Checkbox for whether customer was called
    latitude: '',
    longitude: ''
  });

  const [errors, setErrors] = useState({});
  const [salesExecutives, setSalesExecutives] = useState([]);
  const [impactProducts, setImpactProducts] = useState([]);
  const [banks, setBanks] = useState([]);
  const [branches, setBranches] = useState([]);
  const [isGeolocationEnabled, setIsGeolocationEnabled] = useState(false);

  // Fetch data for dropdowns using the API
  useEffect(() => {
    fetchDropdownData('impact_product', setImpactProducts);
    fetchDropdownData('bank', setBanks);

    if (saleData) {
      setFormData(saleData);
    }

    // Get user's geolocation when the form loads
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setIsGeolocationEnabled(true);
        setFormData((prevData) => ({
          ...prevData,
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        }));
      },
      (error) => {
        toast.error('Please enable location services to proceed.');
        setIsGeolocationEnabled(false);
      }
    );
  }, [saleData]);

  const fetchDropdownData = async (type, setter) => {
    try {
      const response = await axios.get(`/dropdown?type=${type}`);
      setter(response.data);
    } catch (error) {
      toast.error(`Failed to fetch ${type} data`);
    }
  };

  const fetchBranches = async (bankId) => {
    try {
      const response = await axios.get(`/dropdown?type=branch&bank_id=${bankId}`);
      setBranches(response.data);
    } catch (error) {
      toast.error('Failed to fetch branches');
    }
  };

  const fetchSalesExecutives = async (managerId) => {
    try {
      const response = await axios.get(`/dropdown?type=sales_executive&manager_id=${managerId}`);
      setSalesExecutives(response.data);
    } catch (error) {
      toast.error('Failed to fetch sales executives');
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });

    if (name === 'sale_manager_id') {
      fetchSalesExecutives(value);
    }

    if (name === 'bank_id') {
      fetchBranches(value);
    }

    // Handle form dynamically when source type or first_pay_with_momo changes
    if (name === 'source_type') {
      setFormData((prevData) => ({
        ...prevData,
        momo_reference_number: value === 'momo' ? prevData.momo_reference_number : '',
        momo_transaction_id: value === 'momo' ? prevData.momo_transaction_id : '',
        bank_id: value !== 'momo' ? prevData.bank_id : '',
        bank_branch_id: value !== 'momo' ? prevData.bank_branch_id : '',
        bank_acc_number: value !== 'momo' ? prevData.bank_acc_number : '',
        paypoint_name: value === 'paypoint' ? prevData.paypoint_name : '',
        paypoint_branch: value === 'paypoint' ? prevData.paypoint_branch : '',
        staff_id: value !== 'momo' ? prevData.staff_id : '',
        subsequent_pay_source_type: value !== 'momo' ? '' : prevData.subsequent_pay_source_type,
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    if (!formData.sale_manager_id) newErrors.sale_manager_id = 'Sale manager is required';
    if (!formData.sales_executive_id) newErrors.sales_executive_id = 'Sales executive is required';
    if (!formData.client_name) newErrors.client_name = 'Client name is required';
    if (!formData.client_id_no) newErrors.client_id_no = 'Client ID number is required';
    if (!formData.policy_type_id) newErrors.policy_type_id = 'Policy type is required';
    if (!formData.client_phone || formData.client_phone.length !== 10) newErrors.client_phone = 'Valid client phone number is required';
    if (!formData.serial_number) newErrors.serial_number = 'Serial number is required';
    if (!formData.amount) newErrors.amount = 'Amount is required';

    // Validate for Momo transactions
    if (formData.source_type === 'momo') {
      if (!formData.momo_reference_number) newErrors.momo_reference_number = 'Momo reference number is required';
      if (!formData.momo_transaction_id) newErrors.momo_transaction_id = 'Momo transaction ID is required';
      if (!formData.first_pay_with_momo && !formData.subsequent_pay_source_type) newErrors.subsequent_pay_source_type = 'Subsequent payment method is required';
    }

    // Validate for PayPoint transactions
    if (formData.source_type === 'paypoint' || formData.subsequent_pay_source_type === 'paypoint') {
      if (!formData.paypoint_name) newErrors.paypoint_name = 'PayPoint name is required';
      if (!formData.staff_id) newErrors.staff_id = 'Staff ID is required';
    }

    // Validate for Bank transactions
    if (formData.subsequent_pay_source_type === 'bank') {
      if (!formData.bank_id) newErrors.bank_id = 'Bank is required';
      if (!formData.bank_branch_id) newErrors.bank_branch_id = 'Bank branch is required';
      if (!formData.bank_acc_number) newErrors.bank_acc_number = 'Bank account number is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className={isGeolocationEnabled ? '' : 'disabled'}>
      {!isGeolocationEnabled && (
        <div className="text-danger mb-3">Please enable location services to proceed.</div>
      )}

      {/* Sale Manager Field */}
      <div className="form-group">
        <label>Sale Manager</label>
        <select
          className="form-control"
          name="sale_manager_id"
          value={formData.sale_manager_id}
          onChange={handleInputChange}
          disabled={!isGeolocationEnabled}
        >
          <option value="">Select Sale Manager</option>
          {/* Map sale managers here */}
        </select>
        {errors.sale_manager_id && <div className="text-danger">{errors.sale_manager_id}</div>}
      </div>

      {/* Sales Executive Dropdown */}
      <div className="form-group">
        <label>Sales Executive</label>
        <select
          className="form-control"
          name="sales_executive_id"
          value={formData.sales_executive_id}
          onChange={handleInputChange}
          disabled={!isGeolocationEnabled}
        >
          <option value="">Select Sales Executive</option>
          {salesExecutives.map((se) => (
            <option key={se.id} value={se.id}>
              {se.name}
            </option>
          ))}
        </select>
        {errors.sales_executive_id && <div className="text-danger">{errors.sales_executive_id}</div>}
      </div>

      {/* Client Name and Client ID */}
      <div className="form-group">
        <label>Client Name</label>
        <input
          type="text"
          className="form-control"
          name="client_name"
          value={formData.client_name}
          onChange={handleInputChange}
          disabled={!isGeolocationEnabled}
        />
        {errors.client_name && <div className="text-danger">{errors.client_name}</div>}
      </div>

      <div className="form-group">
        <label>Client ID Number</label>
        <input
          type="text"
          className="form-control"
          name="client_id_no"
          value={formData.client_id_no}
          onChange={handleInputChange}
          disabled={!isGeolocationEnabled}
        />
        {errors.client_id_no && <div className="text-danger">{errors.client_id_no}</div>}
      </div>

      {/* Collection Platform */}
      <div className="form-group">
        <label>Collection Platform</label>
        <select
          className="form-control"
          name="collection_platform"
          value={formData.collection_platform}
          onChange={handleInputChange}
          disabled={!isGeolocationEnabled}
        >
          <option value="options">Please select</option>
          <option value="Transflow">Transflow</option>
          <option value="Hubtel">Hubtel</option>
          <option value="company Momo number">Company Momo Number</option>
        </select>
        {errors.collection_platform && <div className="text-danger">{errors.collection_platform}</div>}
      </div>

      {/* Source Type (Momo, Bank, PayPoint) */}
    <div className="form-group">
        <label>Pay Source</label>
        <select
            className="form-control"
            name="source_type"
            value={formData.source_type}
            onChange={handleInputChange}
            disabled={!isGeolocationEnabled}
        >
            <option value="options">Please select</option>
            <option value="momo">Momo</option>
            <option value="bank">Bank</option>
            <option value="paypoint">PayPoint</option>
        </select>
        {errors.source_type && <div className="text-danger">{errors.source_type}</div>}
    </div>

      {/* Momo Transaction Fields */}
      {formData.source_type === 'momo' && (
        <>
          <div className="form-group">
            <label>Momo Reference Number</label>
            <input
              type="text"
              className="form-control"
              name="momo_reference_number"
              value={formData.momo_reference_number}
              onChange={handleInputChange}
              disabled={!isGeolocationEnabled}
            />
            {errors.momo_reference_number && <div className="text-danger">{errors.momo_reference_number}</div>}
          </div>

          <div className="form-group">
            <label>Momo Transaction ID</label>
            <input
              type="text"
              className="form-control"
              name="momo_transaction_id"
              value={formData.momo_transaction_id}
              onChange={handleInputChange}
              disabled={!isGeolocationEnabled}
            />
            {errors.momo_transaction_id && <div className="text-danger">{errors.momo_transaction_id}</div>}
          </div>

          <div className="form-check">
            <input
              type="checkbox"
              className="form-check-input"
              id="first_pay_with_momo"
              name="first_pay_with_momo"
              checked={formData.first_pay_with_momo}
              onChange={handleInputChange}
              disabled={!isGeolocationEnabled}
            />
            <label className="form-check-label" htmlFor="first_pay_with_momo">
              First payment with Momo?
            </label>
          </div>
        </>
      )}

      {/* PayPoint Fields */}
      {formData.source_type === 'paypoint' && (
        <>
          <div className="form-group">
            <label>PayPoint Name</label>
            <input
              type="text"
              className="form-control"
              name="paypoint_name"
              value={formData.paypoint_name}
              onChange={handleInputChange}
              disabled={!isGeolocationEnabled}
            />
            {errors.paypoint_name && <div className="text-danger">{errors.paypoint_name}</div>}
          </div>

          <div className="form-group">
            <label>PayPoint Branch</label>
            <input
              type="text"
              className="form-control"
              name="paypoint_branch"
              value={formData.paypoint_branch}
              onChange={handleInputChange}
              disabled={!isGeolocationEnabled}
            />
            {errors.paypoint_branch && <div className="text-danger">{errors.paypoint_branch}</div>}
          </div>
        </>
      )}

      {/* Bank Fields */}
      {formData.source_type === 'bank' && (
        <>
          <div className="form-group">
            <label>Bank</label>
            <select
              className="form-control"
              name="bank_id"
              value={formData.bank_id}
              onChange={handleInputChange}
              disabled={!isGeolocationEnabled}
            >
              <option value="">Select Bank</option>
              {banks.map((bank) => (
                <option key={bank.id} value={bank.id}>
                  {bank.name}
                </option>
              ))}
            </select>
            {errors.bank_id && <div className="text-danger">{errors.bank_id}</div>}
          </div>

          <div className="form-group">
            <label>Bank Branch</label>
            <select
              className="form-control"
              name="bank_branch_id"
              value={formData.bank_branch_id}
              onChange={handleInputChange}
              disabled={!isGeolocationEnabled}
            >
              <option value="">Select Branch</option>
              {branches.map((branch) => (
                <option key={branch.id} value={branch.id}>
                  {branch.name}
                </option>
              ))}
            </select>
            {errors.bank_branch_id && <div className="text-danger">{errors.bank_branch_id}</div>}
          </div>

          <div className="form-group">
            <label>Bank Account Number</label>
            <input
              type="text"
              className="form-control"
              name="bank_acc_number"
              value={formData.bank_acc_number}
              onChange={handleInputChange}
              disabled={!isGeolocationEnabled}
            />
            {errors.bank_acc_number && <div className="text-danger">{errors.bank_acc_number}</div>}
          </div>
        </>
      )}

      {/* Subsequent Payment */}
      {formData.first_pay_with_momo && (
        <div className="form-group">
          <label>Subsequent Payment Method</label>
          <select
            className="form-control"
            name="subsequent_pay_source_type"
            value={formData.subsequent_pay_source_type}
            onChange={handleInputChange}
            disabled={!isGeolocationEnabled}
          >
            <option value="options">Please select</option>
            <option value="paypoint">PayPoint</option>
            <option value="bank">Bank</option>
          </select>
          {errors.subsequent_pay_source_type && <div className="text-danger">{errors.subsequent_pay_source_type}</div>}
        </div>
      )}

      {/* PayPoint Fields */}
      {formData.subsequent_pay_source_type === 'paypoint' && (
        <>
          <div className="form-group">
            <label>PayPoint Name</label>
            <input
              type="text"
              className="form-control"
              name="paypoint_name"
              value={formData.paypoint_name}
              onChange={handleInputChange}
              disabled={!isGeolocationEnabled}
            />
            {errors.paypoint_name && <div className="text-danger">{errors.paypoint_name}</div>}
          </div>

          <div className="form-group">
            <label>PayPoint Branch</label>
            <input
              type="text"
              className="form-control"
              name="paypoint_branch"
              value={formData.paypoint_branch}
              onChange={handleInputChange}
              disabled={!isGeolocationEnabled}
            />
            {errors.paypoint_branch && <div className="text-danger">{errors.paypoint_branch}</div>}
          </div>
        </>
      )}

      {/* Bank Fields */}
      {formData.subsequent_pay_source_type === 'bank' && (
        <>
          <div className="form-group">
            <label>Bank</label>
            <select
              className="form-control"
              name="bank_id"
              value={formData.bank_id}
              onChange={handleInputChange}
              disabled={!isGeolocationEnabled}
            >
              <option value="">Select Bank</option>
              {banks.map((bank) => (
                <option key={bank.id} value={bank.id}>
                  {bank.name}
                </option>
              ))}
            </select>
            {errors.bank_id && <div className="text-danger">{errors.bank_id}</div>}
          </div>

          <div className="form-group">
            <label>Bank Branch</label>
            <select
              className="form-control"
              name="bank_branch_id"
              value={formData.bank_branch_id}
              onChange={handleInputChange}
              disabled={!isGeolocationEnabled}
            >
              <option value="">Select Branch</option>
              {branches.map((branch) => (
                <option key={branch.id} value={branch.id}>
                  {branch.name}
                </option>
              ))}
            </select>
            {errors.bank_branch_id && <div className="text-danger">{errors.bank_branch_id}</div>}
          </div>

          <div className="form-group">
            <label>Bank Account Number</label>
            <input
              type="text"
              className="form-control"
              name="bank_acc_number"
              value={formData.bank_acc_number}
              onChange={handleInputChange}
              disabled={!isGeolocationEnabled}
            />
            {errors.bank_acc_number && <div className="text-danger">{errors.bank_acc_number}</div>}
          </div>
        </>
      )}

      {/* Staff ID */}
      {(formData.source_type === 'paypoint' || formData.source_type === 'bank' ||formData.subsequent_pay_source_type === 'paypoint' || formData.subsequent_pay_source_type === 'bank') && (
        <div className="form-group">
          <label>Staff Number</label>
          <input
            type="text"
            className="form-control"
            name="staff_id"
            value={formData.staff_id}
            onChange={handleInputChange}
            disabled={!isGeolocationEnabled}
          />
          {errors.staff_id && <div className="text-danger">{errors.staff_id}</div>}
        </div>
      )}

      {/* Customer Called */}
      <div className="form-check">
        <input
          type="checkbox"
          className="form-check-input"
          id="customer_called"
          name="customer_called"
          checked={formData.customer_called}
          onChange={handleInputChange}
          disabled={!isGeolocationEnabled}
        />
        <label className="form-check-label" htmlFor="customer_called">
          Has the customer been called?
        </label>
      </div>

      {/* Amount */}
      <div className="form-group">
        <label>Premium Amount</label>
        <input
          type="number"
          className="form-control"
          name="amount"
          value={formData.amount}
          onChange={handleInputChange}
          disabled={!isGeolocationEnabled}
        />
        {errors.amount && <div className="text-danger">{errors.amount}</div>}
      </div>

      <button type="submit" className="btn btn-primary mt-3" disabled={!isGeolocationEnabled}>
        Submit Sale
      </button>
    </form>
  );
};

export default SalesForm;
