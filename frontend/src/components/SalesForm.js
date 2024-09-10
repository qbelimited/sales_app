import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify'; // For toast notifications

const SalesForm = ({ saleData, onSubmit }) => {
    const [formData, setFormData] = useState({
        sale_manager: '',
        sales_executive_id: '',
        client_name: '',
        client_id_no: '', // Move client ID to the top
        policy_type: '',
        client_phone: '',
        serial_number: '',
        source_type: 'momo',
        momo_reference_number: '',
        momo_transaction_id: '',
        first_pay_with_momo: true,
        subsequent_pay_source_type: '',
        bank_name: '',
        bank_branch: '',
        bank_acc_number: '',
        paypoint_name: '',
        paypoint_branch: '',
        staff_id: '',
        amount: '',
        customer_called: false,
        latitude: '',  // Geolocation
        longitude: ''  // Geolocation
    });

    const [errors, setErrors] = useState({});
    const [salesExecutives, setSalesExecutives] = useState([]);
    const [impactProducts, setImpactProducts] = useState([]);

    useEffect(() => {
        fetchImpactProducts();  // Fetch available Impact Products (Policy Types) on component mount
        if (saleData) {
            setFormData(saleData); // Pre-fill the form if it's an edit
        }

        // Get user’s current geolocation when the form loads
        navigator.geolocation.getCurrentPosition(
            (position) => {
                setFormData((prevData) => ({
                    ...prevData,
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                }));
            },
            (error) => {
                toast.error('Geolocation is not available or permission denied.');
            }
        );
    }, [saleData]);

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
                first_pay_with_momo: value === 'momo' ? true : false,
                client_id_no: prevData.client_id_no,  // Retain client ID regardless of source type
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
        if (!formData.client_id_no) newErrors.client_id_no = 'Client ID number is required'; // Make client ID required
        if (!formData.policy_type) newErrors.policy_type = 'Policy type is required';
        if (!formData.client_phone || formData.client_phone.length !== 10) newErrors.client_phone = 'Valid client phone number is required';
        if (!formData.serial_number) newErrors.serial_number = 'Serial number is required';
        if (!formData.amount) newErrors.amount = 'Amount is required';

        // Validate for Momo transactions
        if (formData.source_type === 'momo') {
            if (!formData.momo_reference_number) newErrors.momo_reference_number = 'Momo reference number is required';
            if (!formData.momo_transaction_id) newErrors.momo_transaction_id = 'Momo transaction ID is required';
        }

        // Validate for Bank transactions
        if (formData.source_type === 'bank') {
            if (!formData.first_pay_with_momo) newErrors.first_pay_with_momo = 'First payment must be with Momo for Bank businesses';
            if (!formData.client_id_no) newErrors.client_id_no = 'Client ID is required for Bank businesses'; // Retained here but always required
            if (!formData.bank_name) newErrors.bank_name = 'Bank name is required';
            if (!formData.bank_branch) newErrors.bank_branch = 'Bank branch is required';
            if (!formData.bank_acc_number) newErrors.bank_acc_number = 'Bank account number is required';
            if (!formData.staff_id) newErrors.staff_id = 'Staff ID is required';
        }

        // Validate for Paypoint transactions
        if (formData.source_type === 'paypoint') {
            if (!formData.paypoint_name) newErrors.paypoint_name = 'Paypoint name is required';
            if (!formData.staff_id) newErrors.staff_id = 'Staff ID is required';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!validateForm()) return;

        onSubmit(formData); // Call onSubmit from parent component

        // Reset form after submission
        setFormData({
            sale_manager: '',
            sales_executive_id: '',
            client_name: '',
            client_id_no: '', // Client ID reset after submission
            policy_type: '',
            client_phone: '',
            serial_number: '',
            source_type: 'momo',
            momo_reference_number: '',
            momo_transaction_id: '',
            first_pay_with_momo: true,
            subsequent_pay_source_type: '',
            bank_name: '',
            bank_branch: '',
            bank_acc_number: '',
            paypoint_name: '',
            paypoint_branch: '',
            staff_id: '',
            amount: '',
            customer_called: false,
            latitude: '',  // Reset latitude after submission
            longitude: ''  // Reset longitude after submission
        });
    };

    return (
        <form onSubmit={handleSubmit}>
            {/* Sale Manager Field */}
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

            {/* Sales Executive Dropdown */}
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

            {/* Client Name Field */}
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

            {/* Client ID Number Field */}
            <div className="form-group">
                <label>Client ID Number</label>
                <input
                    type="text"
                    className="form-control"
                    name="client_id_no"
                    value={formData.client_id_no}
                    onChange={handleInputChange}
                />
                {errors.client_id_no && <div className="text-danger">{errors.client_id_no}</div>}
            </div>

            {/* Policy Type Dropdown */}
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

            {/* Other fields... */}
            {/* Latitude and Longitude Fields (Hidden, but part of formData) */}
            <input type="hidden" name="latitude" value={formData.latitude} />
            <input type="hidden" name="longitude" value={formData.longitude} />

            {/* Submit Button */}
            <button type="submit" className="btn btn-primary mt-3">Submit Sale</button>
        </form>
    );
};

export default SalesForm;
