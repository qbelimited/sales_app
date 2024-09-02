import React, { useState, useEffect } from 'react';
import axios from 'axios';

const SalesForm = () => {
    const [formData, setFormData] = useState({
        sale_manager: '',
        sales_executive_id: '',
        client_phone: '',
        serial_number: '',
        source_type: 'momo', // Default source type
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
    const [sourceTypeOptions, setSourceTypeOptions] = useState(['momo', 'bank', 'paypoint']);

    const handleInputChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData({
            ...formData,
            [name]: type === 'checkbox' ? checked : value,
        });

        // Reset dependent fields if certain fields are changed
        if (name === 'source_type' && value !== 'momo') {
            setFormData((prevData) => ({
                ...prevData,
                momo_reference_number: '',
                momo_transaction_id: '',
                first_pay_with_momo: false,
                subsequent_pay_source_type: '',
            }));
        }
    };

    const validateForm = () => {
        const newErrors = {};
        if (!formData.sale_manager) newErrors.sale_manager = 'Sale manager is required';
        if (!formData.sales_executive_id) newErrors.sales_executive_id = 'Sales executive is required';
        if (!formData.client_phone || formData.client_phone.length !== 10) newErrors.client_phone = 'Valid client phone number is required';
        if (!formData.serial_number) newErrors.serial_number = 'Serial number is required';
        if (!formData.amount) newErrors.amount = 'Amount is required';

        // Specific validation for dynamic fields
        if (formData.source_type === 'momo') {
            if (!formData.momo_reference_number) newErrors.momo_reference_number = 'Momo reference number is required';
            if (!formData.momo_transaction_id) newErrors.momo_transaction_id = 'Momo transaction ID is required';
            if (formData.first_pay_with_momo && !formData.subsequent_pay_source_type) newErrors.subsequent_pay_source_type = 'Subsequent pay source type is required';
        }

        if (formData.source_type === 'bank' || formData.subsequent_pay_source_type === 'bank') {
            if (!formData.bank_name) newErrors.bank_name = 'Bank name is required';
            if (!formData.bank_branch) newErrors.bank_branch = 'Bank branch is required';
            if (!formData.bank_acc_number) newErrors.bank_acc_number = 'Bank account number is required';
        }

        if (formData.source_type === 'paypoint' || formData.subsequent_pay_source_type === 'paypoint') {
            if (!formData.paypoint_name) newErrors.paypoint_name = 'Paypoint name is required';
            if (formData.paypoint_branch) {
                if (!formData.staff_id) newErrors.staff_id = 'Staff ID is required for Paypoint with branch';
            }
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!validateForm()) return;

        try {
            const response = await axios.post('/api/v1/sales', formData);
            alert('Sale submitted successfully');
            setFormData({
                sale_manager: '',
                sales_executive_id: '',
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
            alert('Error submitting sale');
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
            {/* Additional form fields here with similar structure */}
            {/* Example for dynamic fields */}
            <div className="form-group">
                <label>Source Type</label>
                <select
                    className="form-control"
                    name="source_type"
                    value={formData.source_type}
                    onChange={handleInputChange}
                >
                    {sourceTypeOptions.map((option) => (
                        <option key={option} value={option}>
                            {option}
                        </option>
                    ))}
                </select>
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
                </>
            )}
            {/* Add more fields as needed */}
            <button type="submit" className="btn btn-primary mt-3">Submit Sale</button>
        </form>
    );
};

export default SalesForm;
