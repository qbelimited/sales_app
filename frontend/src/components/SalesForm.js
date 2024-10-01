import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import api from '../services/api';

const SalesForm = ({ saleData, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    sale_manager_id: '',
    sales_executive_id: '',
    client_name: '',
    client_id_no: '',
    client_phone: '',
    serial_number: '',
    collection_platform: '',
    source_type: '',
    momo_reference_number: '',
    momo_transaction_id: '',
    first_pay_with_momo: false,
    subsequent_pay_source_type: '',
    bank_id: '',
    bank_branch_id: '',
    bank_acc_number: '',
    paypoint_id: '',
    paypoint_branch: '',
    staff_id: '',
    policy_type_id: '',
    amount: '',
    customer_called: false,
    geolocation_latitude: '',
    geolocation_longitude: '',
    momo_first_premium: false,
    is_deleted: false,  // Soft delete support
    status: 'submitted',
  });

  const [errors, setErrors] = useState({});
  const [salesExecutives, setSalesExecutives] = useState([]);
  const [impactProducts, setImpactProducts] = useState([]);
  const [banks, setBanks] = useState([]);
  const [branches, setBranches] = useState([]);
  const [paypoints, setPaypoints] = useState([]);
  const [salesManagers, setSalesManagers] = useState([]);
  const [isGeolocationEnabled, setIsGeolocationEnabled] = useState(false);

  useEffect(() => {
    fetchBanks();
    fetchImpactProducts();
    fetchSalesManagers();
    fetchPaypoints();

    if (saleData) {
      setFormData(saleData);
    }

    // Get geolocation
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setIsGeolocationEnabled(true);
        setFormData((prevData) => ({
          ...prevData,
          geolocation_latitude: position.coords.latitude,
          geolocation_longitude: position.coords.longitude,
        }));
      },
      () => {
        toast.error('Please enable location services to proceed.');
        setIsGeolocationEnabled(false);
      }
    );
  }, [saleData]);

  // Fetch dropdown data for various fields
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
      toast.error('Failed to fetch branches');
    }
  };

  const fetchSalesExecutives = async (managerId) => {
    try {
      const response = await api.get('/dropdown/', {
        params: { type: 'sales_executive', manager_id: managerId },
      });
      setSalesExecutives(response.data);
    } catch (error) {
      toast.error('Failed to fetch sales executives');
    }
  };

  const fetchSalesManagers = async () => {
    try {
      const response = await api.get('/dropdown/', {
        params: { type: 'users_with_roles', role_id: 4 },
      });
      setSalesManagers(response.data);
    } catch (error) {
      toast.error('Failed to fetch sales managers');
    }
  };

  const fetchPaypoints = async () => {
    try {
      const response = await api.get('/dropdown/', {
        params: { type: 'paypoint' },
      });
      setPaypoints(response.data);
    } catch (error) {
      toast.error('Failed to fetch paypoints');
    }
  };

  const fetchBanks = async () => {
    try {
      const response = await api.get('/bank/');
      setBanks(response.data);
    } catch (error) {
      toast.error('Failed to fetch banks');
    }
  };

  const fetchImpactProducts = async () => {
    try {
      const response = await api.get('/impact_products/');
      setImpactProducts(response.data.products);
    } catch (error) {
      toast.error('Failed to fetch impact products');
    }
  };

  const checkSerialNumberExists = async (serialNumber) => {
    try {
      const response = await api.get('/sales/check-serial', {
        params: { serial_number: serialNumber },
      });
      return response.data.exists; // This returns true/false based on existence
    } catch (error) {
      toast.error('Failed to check serial number');
      return false;
    }
  };

  const handleInputChange = async (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: type === 'checkbox' ? checked : value,
    }));

    if (name === 'serial_number') {
      const exists = await checkSerialNumberExists(value);
      if (exists) {
        toast.error('The serial number already exists.');
        setErrors((prevErrors) => ({
          ...prevErrors,
          serial_number: 'The serial number already exists.',
        }));
      } else {
        setErrors((prevErrors) => ({
          ...prevErrors,
          serial_number: undefined, // Clear the error if it doesn't exist
        }));
      }
    }

    if (name === 'sale_manager_id') {
      fetchSalesExecutives(value);
    }

    if (name === 'bank_id') {
      fetchBranches(value);
    }

    if (name === 'source_type') {
      const isMomo = value === 'momo';
      setFormData((prevData) => ({
        ...prevData,
        momo_reference_number: isMomo ? prevData.momo_reference_number : '',
        momo_transaction_id: isMomo ? prevData.momo_transaction_id : '',
        bank_id: !isMomo ? prevData.bank_id : '',
        bank_branch_id: !isMomo ? prevData.bank_branch_id : '',
        bank_acc_number: !isMomo ? prevData.bank_acc_number : '',
        paypoint_id: value === 'paypoint' ? prevData.paypoint_id : '',
        paypoint_branch: value === 'paypoint' ? prevData.paypoint_branch : '',
        staff_id: !isMomo ? prevData.staff_id : '',
        subsequent_pay_source_type: !isMomo ? '' : prevData.subsequent_pay_source_type,
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
    else if (errors.serial_number) newErrors.serial_number = errors.serial_number;
    if (!formData.amount) newErrors.amount = 'Amount is required';

    // Validate for Momo transactions
    if (formData.source_type === 'momo') {
      if (!formData.momo_reference_number) newErrors.momo_reference_number = 'Momo reference number is required';
      if (!formData.momo_transaction_id) newErrors.momo_transaction_id = 'Momo transaction ID is required';
    }

    // Validate for PayPoint transactions
    if (formData.source_type === 'paypoint' || formData.subsequent_pay_source_type === 'paypoint') {
      if (!formData.paypoint_id) newErrors.paypoint_id = 'PayPoint name is required';
      if (!formData.staff_id) newErrors.staff_id = 'Staff ID is required';
    }

    // Validate for Bank transactions
    if (formData.source_type === 'bank' || formData.subsequent_pay_source_type === 'bank') {
      if (!formData.bank_id) newErrors.bank_id = 'Bank is required';
      if (!formData.bank_branch_id) newErrors.bank_branch_id = 'Bank branch is required';
      if (!formData.bank_acc_number) {
        newErrors.bank_acc_number = 'Bank account number is required';
      } else {
        const length = formData.bank_acc_number.length;
        const bankName = formData.bank_id || '';

        // Bank-specific validation
        const lowerCaseBankName = bankName.toLowerCase(); // Convert bank name to lower case for case-insensitive comparison
        if (lowerCaseBankName.includes('uba') && length !== 14) {
          newErrors.bank_acc_number = 'UBA account number must be 14 digits';
        } else if ((lowerCaseBankName.includes('zenith') || lowerCaseBankName.includes('absa')) && length !== 10) {
          newErrors.bank_acc_number = 'Zenith or Absa account number must be 10 digits';
        } else if (lowerCaseBankName.includes('sg') && length !== 12 && length !== 13) {
          newErrors.bank_acc_number = 'SG account number must be 12 or 13 digits';
        } else if (length !== 13 && length !== 16) {
          newErrors.bank_acc_number = 'Account number must be 13 or 16 digits';
        }
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Ensure form is valid
    if (!validateForm()) return;

    try {
      // Sanitize and prepare data
      const sanitizedData = {
        ...formData,
        sale_manager_id: parseInt(formData.sale_manager_id, 10),  // Convert to integer
        sales_executive_id: parseInt(formData.sales_executive_id, 10),  // Convert to integer
        policy_type_id: parseInt(formData.policy_type_id, 10),  // Convert to integer
        amount: parseFloat(formData.amount),  // Convert amount to float

        // Conditionally convert to integer if value exists, otherwise omit
        bank_id: formData.bank_id ? parseInt(formData.bank_id, 10) : undefined,
        bank_branch_id: formData.bank_branch_id ? parseInt(formData.bank_branch_id, 10) : undefined,
        paypoint_id: formData.paypoint_id ? parseInt(formData.paypoint_id, 10) : undefined,

        // Destructure and prepare geolocation
        geolocation: {
          latitude: parseFloat(formData.geolocation_latitude),
          longitude: parseFloat(formData.geolocation_longitude),
        },
      };

      // Remove any undefined fields from sanitizedData
      Object.keys(sanitizedData).forEach(key => {
        if (sanitizedData[key] === undefined) {
            delete sanitizedData[key];
        }
      });

      // Make API request to submit the sale
      const response = await api.post('/sales/', sanitizedData, {
        headers: {
          'Content-Type': 'application/json', // Ensure the correct content type
        },
      });

      // Check if response is successful
      if (response.status === 201 || response.status === 200 || response.status === 415 || response.status === 204) {
        toast.success('Sale submitted successfully!');
        onSubmit();  // Optionally handle success callback or redirect
      } else {
        toast.error('Failed to submit the sale. Please try again.');
      }
    } catch (error) {
      console.error('Error submitting sale:', error);
      toast.error('Failed to submit the sale');
    }
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
          {salesManagers.map((sm) => (
            <option key={sm.id} value={sm.id}>
              {sm.name}
            </option>
          ))}
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
        <label>Client Phone Number</label>
        <input
          type="text"
          className="form-control"
          name="client_phone"
          value={formData.client_phone}
          onChange={handleInputChange}
          disabled={!isGeolocationEnabled}
        />
        {errors.client_phone && <div className="text-danger">{errors.client_phone}</div>}
      </div>

      <div className="form-group">
        <label>Client Ghana Card ID No. ("no hyphens" - e.g. 'GHA123435555')</label>
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
          <option value="">Please select</option>
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
              <option value="">Please select</option>
              <option value="Transflow">Transflow</option>
              <option value="Hubtel">Hubtel</option>
              <option value="company Momo number">Company Momo Number</option>
            </select>
            {errors.collection_platform && <div className="text-danger">{errors.collection_platform}</div>}
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
            <select
              type="text"
              className="form-control"
              name="paypoint_id"
              value={formData.paypoint_id}
              onChange={handleInputChange}
              disabled={!isGeolocationEnabled}
            >
              <option value="">Select Paypoint</option>
              {paypoints.map((ppy) => (
                <option key={ppy.id} value={ppy.id}>
                  {ppy.name}
                </option>
              ))}
            </select>
            {errors.paypoint_id && <div className="text-danger">{errors.paypoint_id}</div>}
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

          {/* Branch Selection - Updates when a bank is selected */}
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

      {/* Impact Products Dropdown (previously missing) */}
      <div className="form-group">
        <label>Policy Type (Impact Product)</label>
        <select
          className="form-control"
          name="policy_type_id"
          value={formData.policy_type_id}
          onChange={handleInputChange}
          disabled={!isGeolocationEnabled}
        >
          <option value="">Select Product</option>
          {impactProducts.map((product) => (
            <option key={product.id} value={product.id}>
              {product.name}
            </option>
          ))}
        </select>
        {errors.policy_type_id && <div className="text-danger">{errors.policy_type_id}</div>}
      </div>

      {/* Policy Form Serial Number (previously missing) */}
      <div className="form-group">
        <label>Policy Form Serial Number</label>
        <input
          className="form-control"
          name="serial_number"
          value={formData.serial_number}
          onChange={handleInputChange}
          disabled={!isGeolocationEnabled}
        />
        {errors.serial_number && <div className="text-danger">{errors.serial_number}</div>}
      </div>

      {/* Subsequent Payment Dropdown */}
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

      {/* PayPoint Fields for Subsequent Payment */}
      {formData.subsequent_pay_source_type === 'paypoint' && (
        <>
          <div className="form-group">
            <label>PayPoint Name</label>
            <select
              type="text"
              className="form-control"
              name="paypoint_id"
              value={formData.paypoint_id}
              onChange={handleInputChange}
              disabled={!isGeolocationEnabled}
            >
              <option value="">Select Paypoint</option>
              {paypoints.map((ppy) => (
                <option key={ppy.id} value={ppy.id}>
                  {ppy.name}
                </option>
              ))}
            </select>
            {errors.paypoint_id && <div className="text-danger">{errors.paypoint_id}</div>}
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

      {/* Bank Fields for Subsequent Payment */}
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

          {/* Branch Selection - Updates when a bank is selected */}
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
      {(formData.source_type === 'paypoint' || formData.subsequent_pay_source_type === 'paypoint') && (
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

      <div style={{ color: 'red', fontSize: '11px'}}>
        <em>Premium amounts are strictly in Ghana Cedis (GHS)</em>
      </div>

      <button type="submit" className="btn btn-primary mt-3">
        Submit Sale
      </button>
      <button type="button" className="btn btn-secondary mt-3 ml-2" onClick={onCancel}>
        Cancel
      </button>
    </form>
  );
};

export default SalesForm;
