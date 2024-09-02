import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify'; // For toast notifications

const SalesForm = () => {
    const [formData, setFormData] = useState({
        sale_manager: '',
        sales_executive_id: '',
        client_name: '',
        policy_type: '',
        client_phone: '',
        serial_number: '',
        source_type: 'momo',
        momo_reference_number: '',
        momo_transaction_id: '',
        first_pay_with_momo: false,
        subsequent_pay_source_type: '',
        bank_name: '',
        bank_branch: '',
        bank_acc_number: '',
        paypoint_name: '',
        paypoint_branch: '',
        staff_id: '',
        amount: '',
        customer_called: false,
    });

    const [errors, setErrors] = useState({});
    const [salesExecutives, setSalesExecutives] = useState([]);
    const [impactProducts, setImpactProducts] = useState([]);

    useEffect(() => {
        fetchImpactProducts();  // Fetch available Impact Products (Policy Types) on component mount
    }, []);

    const fetchImpactProducts = async () => {
        try {
            const response = await axios.get('/api/v1/dropdown', {
                params: { type: 'impact_product' }
            });
            setImpactProducts(response.data);
        } catch (error) {
            console.error('Failed to fetch impact products:', error);
            toast.error('Failed to fetch policy types');
        }
    };

    const handleInputChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData({
            ...formData,
            [name]: type === 'checkbox' ? checked : value,
        });

        // Fetch sales executives if the sales manager changes
        if (name === 'sale_manager') {
            fetchSalesExecutives(value);
        }

        // Reset dependent fields if certain fields are changed
        if (name === 'source_type') {
            setFormData((prevData) => ({
                ...prevData,
                momo_reference_number: value === 'momo' ? prevData.momo_reference_number : '',
                momo_transaction_id: value === 'momo' ? prevData.momo_transaction_id : '',
                first_pay_with_momo: value === 'momo' ? prevData.first_pay_with_momo : false,
                subsequent_pay_source_type: value === 'momo' ? prevData.subsequent_pay_source_type : '',
                bank_name: value !== 'momo' ? prevData.bank_name : '',
                bank_branch: value !== 'momo' ? prevData.bank_branch : '',
                bank_acc_number: value !== 'momo' ? prevData.bank_acc_number : '',
                paypoint_name: value === 'paypoint' ? prevData.paypoint_name : '',
                paypoint_branch: value === 'paypoint' ? prevData.paypoint_branch : '',
                staff_id: value !== 'momo' ? prevData.staff_id : '',
            }));
        }
    };

    const fetchSalesExecutives = async (managerId) => {
        try {
            const response = await axios.get('/api/v1/dropdown', {
                params: { type: 'sales_executive', manager_id: managerId }
            });
            setSalesExecutives(response.data);
            setFormData((prevData) => ({ ...prevData, sales_executive_id: '' }));
        } catch (error) {
            console.error('Failed to fetch sales executives:', error);
            toast.error('Failed to fetch sales executives');
        }
    };

    const validateForm = () => {
        const newErrors = {};
        if (!formData.sale_manager) newErrors.sale_manager = 'Sale manager is required';
        if (!formData.sales_executive_id) newErrors.sales_executive_id = 'Sales executive is required';
        if (!formData.client_name) newErrors.client_name = 'Client name is required';
        if (!formData.policy_type) newErrors.policy_type = 'Policy type is required';
        if (!formData.client_phone || formData.client_phone.length !== 10) newErrors.client_phone = 'Valid client phone number is required';
        if (!formData.serial_number) newErrors.serial_number = 'Serial number is required';
        if (!formData.amount) newErrors.amount = 'Amount is required';

        if (formData.source_type === 'momo') {
            if (!formData.momo_reference_number) newErrors.momo_reference_number = 'Momo reference number is required';
            if (!formData.momo_transaction_id) newErrors.momo_transaction_id = 'Momo transaction ID is required';
            if (formData.first_pay_with_momo && !formData.subsequent_pay_source_type) {
                newErrors.subsequent_pay_source_type = 'Subsequent pay source type is required';
            }
        } else if (formData.source_type === 'bank') {
            if (!formData.bank_name) newErrors.bank_name = 'Bank name is required';
            if (!formData.bank_branch) newErrors.bank_branch = 'Bank branch is required';
            if (!formData.bank_acc_number) newErrors.bank_acc_number = 'Bank account number is required';
            if (!formData.staff_id) newErrors.staff_id = 'Staff ID is required';
        } else if (formData.source_type === 'paypoint') {
            if (!formData.paypoint_name) newErrors.paypoint_name = 'Paypoint name is required';
            if (!formData.staff_id) newErrors.staff_id = 'Staff ID is required';
        }

        if (formData.subsequent_pay_source_type === 'bank' && formData.first_pay_with_momo) {
            if (!formData.bank_name) newErrors.bank_name = 'Bank name is required for subsequent payment';
            if (!formData.bank_branch) newErrors.bank_branch = 'Bank branch is required for subsequent payment';
            if (!formData.bank_acc_number) newErrors.bank_acc_number = 'Bank account number is required for subsequent payment';
            if (!formData.staff_id) newErrors.staff_id = 'Staff ID is required for subsequent payment';
        } else if (formData.subsequent_pay_source_type === 'paypoint' && formData.first_pay_with_momo) {
            if (!formData.paypoint_name) newErrors.paypoint_name = 'Paypoint name is required for subsequent payment';
            if (!formData.staff_id) newErrors.staff_id = 'Staff ID is required for subsequent payment';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!validateForm()) return;

        try {
            await axios.post('/api/v1/sales', formData);
            toast.success('Sale submitted successfully');
            setFormData({
                sale_manager: '',
                sales_executive_id: '',
                client_name: '',
                policy_type: '',
                client_phone: '',
                serial_number: '',
                source_type: 'momo',
                momo_reference_number: '',
                momo_transaction_id: '',
                first_pay_with_momo: false,
                subsequent_pay_source_type: '',
                bank_name: '',
                bank_branch: '',
                bank_acc_number: '',
                paypoint_name: '',
                paypoint_branch: '',
                staff_id: '',
                amount: '',
                customer_called: false,
            });
        } catch (error) {
            console.error('Error submitting sale:', error);
            toast.error('Error submitting sale');
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <div className="form-group">
                <label>Sale Manager</label>
                <input
                    type="text"
                    className="form-control"
                    name="sale_manager"
                    value={formData.sale_manager}
                    onChange={handleInputChange}
                />
                {errors.sale_manager && <div className="text-danger">{errors.sale_manager}</div>}
            </div>

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

            <div className="form-group">
                <label>Policy Type</label>
                <select
                    className="form-control"
                    name="policy_type"
                    value={formData.policy_type}
                    onChange={handleInputChange}
                >
                    <option value="">Select Policy Type</option>
                    {impactProducts.map((product) => (
                        <option key={product.id} value={product.id}>
                            {product.name}
                        </option>
                    ))}
                </select>
                {errors.policy_type && <div className="text-danger">{errors.policy_type}</div>}
            </div>

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

            <div className="form-group">
                <label>Serial Number</label>
                <input
                    type="text"
                    className="form-control"
                    name="serial_number"
                    value={formData.serial_number}
                    onChange={handleInputChange}
                />
                {errors.serial_number && <div className="text-danger">{errors.serial_number}</div>}
            </div>

            <div className="form-group">
                <label>Source Type</label>
                <select
                    className="form-control"
                    name="source_type"
                    value={formData.source_type}
                    onChange={handleInputChange}
                >
                    <option value="momo">Momo</option>
                    <option value="bank">Bank</option>
                    <option value="paypoint">Paypoint</option>
                </select>
                {errors.source_type && <div className="text-danger">{errors.source_type}</div>}
            </div>

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

                    <div className="form-group">
                        <label>
                            <input
                                type="checkbox"
                                name="first_pay_with_momo"
                                checked={formData.first_pay_with_momo}
                                onChange={handleInputChange}
                            />
                            {' '}First Pay with Momo?
                        </label>
                    </div>

                    {formData.first_pay_with_momo && (
                        <div className="form-group">
                            <label>Subsequent Pay Source Type</label>
                            <select
                                className="form-control"
                                name="subsequent_pay_source_type"
                                value={formData.subsequent_pay_source_type}
                                onChange={handleInputChange}
                            >
                                <option value="">Select Subsequent Pay Source</option>
                                <option value="bank">Bank</option>
                                <option value="paypoint">Paypoint</option>
                            </select>
                            {errors.subsequent_pay_source_type && <div className="text-danger">{errors.subsequent_pay_source_type}</div>}
                        </div>
                    )}

                    {formData.subsequent_pay_source_type === 'bank' && (
                        <>
                            <div className="form-group">
                                <label>Bank Name</label>
                                <input
                                    type="text"
                                    className="form-control"
                                    name="bank_name"
                                    value={formData.bank_name}
                                    onChange={handleInputChange}
                                />
                                {errors.bank_name && <div className="text-danger">{errors.bank_name}</div>}
                            </div>

                            <div className="form-group">
                                <label>Bank Branch</label>
                                <input
                                    type="text"
                                    className="form-control"
                                    name="bank_branch"
                                    value={formData.bank_branch}
                                    onChange={handleInputChange}
                                />
                                {errors.bank_branch && <div className="text-danger">{errors.bank_branch}</div>}
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

                            <div className="form-group">
                                <label>Staff ID</label>
                                <input
                                    type="text"
                                    className="form-control"
                                    name="staff_id"
                                    value={formData.staff_id}
                                    onChange={handleInputChange}
                                />
                                {errors.staff_id && <div className="text-danger">{errors.staff_id}</div>}
                            </div>
                        </>
                    )}

                    {formData.subsequent_pay_source_type === 'paypoint' && (
                        <>
                            <div className="form-group">
                                <label>Paypoint Name</label>
                                <input
                                    type="text"
                                    className="form-control"
                                    name="paypoint_name"
                                    value={formData.paypoint_name}
                                    onChange={handleInputChange}
                                />
                                {errors.paypoint_name && <div className="text-danger">{errors.paypoint_name}</div>}
                            </div>

                            <div className="form-group">
                                <label>Paypoint Branch</label>
                                <input
                                    type="text"
                                    className="form-control"
                                    name="paypoint_branch"
                                    value={formData.paypoint_branch}
                                    onChange={handleInputChange}
                                />
                            </div>

                            <div className="form-group">
                                <label>Staff ID</label>
                                <input
                                    type="text"
                                    className="form-control"
                                    name="staff_id"
                                    value={formData.staff_id}
                                    onChange={handleInputChange}
                                />
                                {errors.staff_id && <div className="text-danger">{errors.staff_id}</div>}
                            </div>
                        </>
                    )}
                </>
            )}

            {formData.source_type === 'bank' && (
                <>
                    <div className="form-group">
                        <label>Bank Name</label>
                        <input
                            type="text"
                            className="form-control"
                            name="bank_name"
                            value={formData.bank_name}
                            onChange={handleInputChange}
                        />
                        {errors.bank_name && <div className="text-danger">{errors.bank_name}</div>}
                    </div>

                    <div className="form-group">
                        <label>Bank Branch</label>
                        <input
                            type="text"
                            className="form-control"
                            name="bank_branch"
                            value={formData.bank_branch}
                            onChange={handleInputChange}
                        />
                        {errors.bank_branch && <div className="text-danger">{errors.bank_branch}</div>}
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

                    <div className="form-group">
                        <label>Staff ID</label>
                        <input
                            type="text"
                            className="form-control"
                            name="staff_id"
                            value={formData.staff_id}
                            onChange={handleInputChange}
                        />
                        {errors.staff_id && <div className="text-danger">{errors.staff_id}</div>}
                    </div>
                </>
            )}

            {formData.source_type === 'paypoint' && (
                <>
                    <div className="form-group">
                        <label>Paypoint Name</label>
                        <input
                            type="text"
                            className="form-control"
                            name="paypoint_name"
                            value={formData.paypoint_name}
                            onChange={handleInputChange}
                        />
                        {errors.paypoint_name && <div className="text-danger">{errors.paypoint_name}</div>}
                    </div>

                    <div className="form-group">
                        <label>Paypoint Branch</label>
                        <input
                            type="text"
                            className="form-control"
                            name="paypoint_branch"
                            value={formData.paypoint_branch}
                            onChange={handleInputChange}
                        />
                    </div>

                    <div className="form-group">
                        <label>Staff ID</label>
                        <input
                            type="text"
                            className="form-control"
                            name="staff_id"
                            value={formData.staff_id}
                            onChange={handleInputChange}
                        />
                        {errors.staff_id && <div className="text-danger">{errors.staff_id}</div>}
                    </div>
                </>
            )}

            <div className="form-group">
                <label>Amount</label>
                <input
                    type="number"
                    className="form-control"
                    name="amount"
                    value={formData.amount}
                    onChange={handleInputChange}
                />
                {errors.amount && <div className="text-danger">{errors.amount}</div>}
            </div>

            <div className="form-group">
                <label>
                    <input
                        type="checkbox"
                        name="customer_called"
                        checked={formData.customer_called}
                        onChange={handleInputChange}
                    />
                    {' '}Customer Called?
                </label>
            </div>

            <button type="submit" className="btn btn-primary mt-3">Submit Sale</button>
        </form>
    );
};

export default SalesForm;
