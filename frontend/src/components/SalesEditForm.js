import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import api from '../services/api';

const SalesEditForm = ({ saleData, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    sale_manager_id: saleData?.sale_manager?.id || '',
    sales_executive_id: saleData?.sales_executive_id || '',
    client_name: saleData?.client_name || '',
    client_id_no: saleData?.client_id_no || '',
    client_phone: saleData?.client_phone || '',
    serial_number: saleData?.serial_number || '',
    collection_platform: saleData?.collection_platform || '',
    source_type: saleData?.source_type || '',
    momo_reference_number: saleData?.momo_reference_number || '',
    momo_transaction_id: saleData?.momo_transaction_id || '',
    first_pay_with_momo: saleData?.first_pay_with_momo || false,
    subsequent_pay_source_type: saleData?.subsequent_pay_source_type || '',
    bank_id: saleData?.bank?.id || '',
    bank_branch_id: saleData?.bank_branch?.id || '',
    bank_acc_number: saleData?.bank_acc_number || '',
    paypoint_id: saleData?.paypoint?.id || '',
    paypoint_branch: saleData?.paypoint_branch || '',
    staff_id: saleData?.staff_id || '',
    policy_type_id: saleData?.policy_type?.id || '',
    amount: saleData?.amount || '',
    customer_called: saleData?.customer_called || false,
    geolocation_latitude: saleData?.geolocation_latitude || '',
    geolocation_longitude: saleData?.geolocation_longitude || '',
    status: saleData?.status || 'submitted',
  });

  const [errors, setErrors] = useState({});
  const [salesExecutives, setSalesExecutives] = useState([]);
  const [salesManagers, setSalesManagers] = useState([]);
  const [branches, setBranches] = useState([]);
  const [banks, setBanks] = useState([]);
  const [paypoints, setPaypoints] = useState([]);
  const [policyTypes, setPolicyTypes] = useState([]);

  useEffect(() => {
    fetchDropdownData();
    if (saleData.bank_id) fetchBranches(saleData.bank_id);
    if (saleData.sale_manager_id) fetchSalesExecutives(saleData.sale_manager_id);
  }, [saleData]);

  const fetchDropdownData = async () => {
    try {
      const [managerResponse, bankResponse, paypointResponse, policyResponse] = await Promise.all([
        api.get('/dropdown/', { params: { type: 'users_with_roles', role_id: 4 } }), // Sales Managers
        api.get('/bank/'), // Banks
        api.get('/dropdown/', { params: { type: 'paypoint' } }), // Paypoints
        api.get('/impact_products/'), // Policy Types
      ]);

      setSalesManagers(managerResponse.data);
      setBanks(bankResponse.data);
      setPaypoints(paypointResponse.data);
      setPolicyTypes(policyResponse.data.products);
    } catch (error) {
      toast.error('Failed to fetch dropdown data');
    }
  };

  const fetchBranches = async (bankId) => {
    try {
      const response = await api.get('/dropdown/', {
        params: { type: 'branch', bank_id: bankId },
      });
      setBranches(response.data);
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

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: type === 'checkbox' ? checked : value,
    }));

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
    if (!formData.amount) newErrors.amount = 'Amount is required';

    // Validate for Momo transactions
    if (formData.source_type === 'momo') {
      if (!formData.momo_reference_number) newErrors.momo_reference_number = 'Momo reference number is required';
      if (!formData.momo_transaction_id) newErrors.momo_transaction_id = 'Momo transaction ID is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) return;

    try {
      const sanitizedData = {
        ...formData,
        sale_manager_id: parseInt(formData.sale_manager_id, 10),
        sales_executive_id: parseInt(formData.sales_executive_id, 10),
        policy_type_id: parseInt(formData.policy_type_id, 10),
        amount: parseFloat(formData.amount),
        bank_id: formData.bank_id ? parseInt(formData.bank_id, 10) : undefined,
        bank_branch_id: formData.bank_branch_id ? parseInt(formData.bank_branch_id, 10) : undefined,
        paypoint_id: formData.paypoint_id ? parseInt(formData.paypoint_id, 10) : undefined,
        geolocation_latitude: parseFloat(formData.geolocation_latitude),
        geolocation_longitude: parseFloat(formData.geolocation_longitude),
      };

      Object.keys(sanitizedData).forEach((key) => {
        if (sanitizedData[key] === undefined) {
          delete sanitizedData[key];
        }
      });

      // API request for updating the sale using PUT method
      const response = await api.put(`/sales/${saleData.id}`, sanitizedData);

      if (response.status === 200) {
        toast.success('Sale updated successfully!');
        onSubmit();
      } else {
        // toast.error('Failed to update the sale. Please try again.');
      }
    } catch (error) {
      // toast.error('Failed to update the sale');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Sale Manager */}
      <div className="form-group">
        <label>Sale Manager</label>
        <select
          className="form-control"
          name="sale_manager_id"
          value={formData.sale_manager_id}
          onChange={handleInputChange}
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

      {/* Sales Executive */}
      <div className="form-group">
        <label>Sales Executive</label>
        <select
          className="form-control"
          name="sales_executive_id"
          value={formData.sales_executive_id}
          onChange={handleInputChange}
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

      {/* Client Name */}
      <div className="form-group">
        <label>Client Name</label>
        <input
          type="text"
          className="form-control"
          name="client_name"
          value={formData.client_name}
          onChange={handleInputChange}
        />
        {errors.client_name && <div className="text-danger">{errors.client_name}</div>}
      </div>

      {/* Client Phone */}
      <div className="form-group">
        <label>Client Phone</label>
        <input
          type="text"
          className="form-control"
          name="client_phone"
          value={formData.client_phone}
          onChange={handleInputChange}
        />
        {errors.client_phone && <div className="text-danger">{errors.client_phone}</div>}
      </div>

      {/* Client Ghana Card ID No */}
      <div className="form-group">
        <label>Client Ghana Card ID No</label>
        <input
          type="text"
          className="form-control"
          name="client_id_no"
          value={formData.client_id_no}
          onChange={handleInputChange}
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
        >
          <option value="">Please select</option>
          <option value="momo">Momo</option>
          <option value="bank">Bank</option>
          <option value="paypoint">PayPoint</option>
        </select>
        {errors.source_type && <div className="text-danger">{errors.source_type}</div>}
      </div>

      {/* Momo Information */}
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
            />
            {errors.momo_transaction_id && <div className="text-danger">{errors.momo_transaction_id}</div>}
          </div>
        </>
      )}

      {/* Bank Information */}
      {formData.source_type === 'bank' && (
        <>
          <div className="form-group">
            <label>Bank</label>
            <select
              className="form-control"
              name="bank_id"
              value={formData.bank_id}
              onChange={handleInputChange}
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
            />
            {errors.bank_acc_number && <div className="text-danger">{errors.bank_acc_number}</div>}
          </div>
        </>
      )}

      {/* Policy Type */}
      <div className="form-group">
        <label>Policy Type</label>
        <select
          className="form-control"
          name="policy_type_id"
          value={formData.policy_type_id}
          onChange={handleInputChange}
        >
          <option value="">Select Policy Type</option>
          {policyTypes.map((policy) => (
            <option key={policy.id} value={policy.id}>
              {policy.name}
            </option>
          ))}
        </select>
        {errors.policy_type_id && <div className="text-danger">{errors.policy_type_id}</div>}
      </div>

      {/* PayPoint Information */}
      {formData.source_type === 'paypoint' && (
        <>
          <div className="form-group">
            <label>PayPoint</label>
            <select
              className="form-control"
              name="paypoint_id"
              value={formData.paypoint_id}
              onChange={handleInputChange}
            >
              <option value="">Select PayPoint</option>
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
            />
            {errors.paypoint_branch && <div className="text-danger">{errors.paypoint_branch}</div>}
          </div>
        </>
      )}

      {/* Subsequent Payment Method */}
      {formData.first_pay_with_momo && (
        <div className="form-group">
          <label>Subsequent Payment Source Type</label>
          <select
            className="form-control"
            name="subsequent_pay_source_type"
            value={formData.subsequent_pay_source_type}
            onChange={handleInputChange}
          >
            <option value="">Select Subsequent Payment Method</option>
            <option value="paypoint">PayPoint</option>
            <option value="bank">Bank</option>
          </select>
        </div>
      )}

      {/* Amount */}
      <div className="form-group">
        <label>Amount</label>
        <input
          type="text"
          className="form-control"
          name="amount"
          value={formData.amount}
          onChange={handleInputChange}
        />
        {errors.amount && <div className="text-danger">{errors.amount}</div>}
      </div>

      {/* Submit and Cancel buttons */}
      <button type="submit" className="btn btn-primary mt-3">
        Update Sale
      </button>
      <button type="button" className="btn btn-secondary mt-3 ml-2" onClick={onCancel}>
        Cancel
      </button>
    </form>
  );
};

export default SalesEditForm;
