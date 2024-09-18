// SaleDetailsPage.js
import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Spinner, Card, Container, Row, Col, Button } from 'react-bootstrap';
import api from '../services/api';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-defaulticon-compatibility';
import 'leaflet-defaulticon-compatibility/dist/leaflet-defaulticon-compatibility.css';

const SaleDetailsPage = () => {
    const { saleId } = useParams(); // Extract saleId from the URL
    const navigate = useNavigate(); // Use navigate to go back to the sales list
    const [saleDetails, setSaleDetails] = useState(null);
    const [salesExecutive, setSalesExecutive] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchSaleDetails = async () => {
            try {
                const response = await api.get(`/sales/${saleId}`);
                setSaleDetails(response.data);

                // Fetch the sales executive details using the sales_executive_id from saleDetails
                if (response.data.sales_executive_id) {
                    const executiveResponse = await api.get(`/sales_executives/${response.data.sales_executive_id}`);
                    setSalesExecutive(executiveResponse.data);
                }
            } catch (error) {
                console.error('Error fetching sale details:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchSaleDetails();
    }, [saleId]);

    if (loading) {
        return (
            <div className="text-center mt-5">
                <Spinner animation="border" />
            </div>
        );
    }

    if (!saleDetails) {
        return <div className="text-center mt-5">Sale details not available.</div>;
    }

    // Helper function to render a field if it has data
    const renderField = (label, value) => {
        return value ? (
            <Card.Text><strong>{label}: </strong>{value}</Card.Text>
        ) : null;
    };

    return (
        <Container className="mt-5">
            <Button variant="secondary" onClick={() => navigate(-1)} className="mb-4">Back to Sales</Button> {/* Back button */}
            <h2 className="mb-4 text-center">Sale Details</h2>
            <Row>
                <Col md={6}>
                    <Card className="mb-4 shadow-sm">
                        <Card.Header className="bg-primary text-white">
                            General Information
                        </Card.Header>
                        <Card.Body>
                            {renderField('Client Name', saleDetails.client_name)}
                            {renderField('Client ID No', saleDetails.client_id_no)}
                            {renderField('Client Phone', saleDetails.client_phone)}
                            {renderField('Serial Number', saleDetails.serial_number)}
                            {renderField('Source Type', saleDetails.source_type)}
                            {renderField('Policy Type', saleDetails.policy_type?.name)}
                            {renderField('Amount', `GHS ${saleDetails.amount}`)}
                            {renderField('Sales Executive', `${salesExecutive?.name} (Code: ${salesExecutive?.code})`)}
                            {renderField('Sales Manager', saleDetails.sale_manager?.name)}
                            {renderField('Date & Time', new Date(saleDetails.created_at).toLocaleString())}
                            {renderField('Staff ID', saleDetails?.staff_id)}
                            {renderField('Status', saleDetails.status)}
                            {renderField('Customer Called', saleDetails.customer_called ? 'Yes' : 'No')}
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={6}>
                    {/* Momo Payment Information */}
                    {(saleDetails.momo_reference_number || saleDetails.momo_transaction_id || saleDetails.first_pay_with_momo) && (
                        <Card className="mb-4 shadow-sm">
                            <Card.Header className="bg-primary text-white">
                                Momo Payment Information
                            </Card.Header>
                            <Card.Body>
                                {renderField('Momo Reference Number', saleDetails.momo_reference_number)}
                                {renderField('Momo Transaction ID', saleDetails.momo_transaction_id)}
                                {renderField('First Pay with Momo', saleDetails.first_pay_with_momo ? 'Yes' : 'No')}
                            </Card.Body>
                        </Card>
                    )}

                    {/* Bank Payment Information */}
                    {(saleDetails.bank?.name || saleDetails.bank_branch?.name || saleDetails.bank_acc_number) && (
                        <Card className="mb-4 shadow-sm">
                            <Card.Header className="bg-primary text-white">
                                Bank Payment Information
                            </Card.Header>
                            <Card.Body>
                                {renderField('Bank', saleDetails.bank?.name)}
                                {renderField('Bank Branch', saleDetails.bank_branch?.name)}
                                {renderField('Bank Account Number', saleDetails.bank_acc_number)}
                            </Card.Body>
                        </Card>
                    )}

                    {/* Paypoint Payment Information */}
                    {(saleDetails.paypoint?.name || saleDetails.paypoint_branch) && (
                        <Card className="mb-4 shadow-sm">
                            <Card.Header className="bg-primary text-white">
                                Paypoint Payment Information
                            </Card.Header>
                            <Card.Body>
                                {renderField('Paypoint', saleDetails.paypoint?.name)}
                                {renderField('Paypoint Branch', saleDetails.paypoint_branch)}
                            </Card.Body>
                        </Card>
                    )}

                    {/* Subsequent Payment Information */}
                    {saleDetails.subsequent_pay_source_type && (
                        <Card className="mb-4 shadow-sm">
                            <Card.Header className="bg-primary text-white">
                                Subsequent Payment Information
                            </Card.Header>
                            <Card.Body>
                                {renderField('Subsequent Pay Source Type', saleDetails.subsequent_pay_source_type)}
                                {/* Include additional bank or paypoint information if available */}
                                {renderField('Subsequent Bank', saleDetails.subsequent_bank?.name)}
                                {renderField('Subsequent Bank Branch', saleDetails.subsequent_bank_branch?.name)}
                                {renderField('Subsequent Bank Account Number', saleDetails.subsequent_bank_acc_number)}
                                {renderField('Subsequent Paypoint', saleDetails.subsequent_paypoint?.name)}
                                {renderField('Subsequent Paypoint Branch', saleDetails.subsequent_paypoint_branch)}
                            </Card.Body>
                        </Card>
                    )}
                </Col>
            </Row>

            {/* Map for Geolocation */}
            {saleDetails.geolocation_latitude && saleDetails.geolocation_longitude && (
                <Card className="mt-4 shadow-sm">
                    <Card.Header className="bg-primary text-white">
                        Location
                    </Card.Header>
                    <Card.Body>
                        <MapContainer
                            style={{ height: '300px', width: '100%' }}
                            center={[saleDetails.geolocation_latitude, saleDetails.geolocation_longitude]}
                            zoom={13}
                        >
                            <TileLayer
                                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                            />
                            <Marker position={[saleDetails.geolocation_latitude, saleDetails.geolocation_longitude]}>
                                <Popup>
                                    Sale Location
                                </Popup>
                            </Marker>
                        </MapContainer>
                    </Card.Body>
                </Card>
            )}
        </Container>
    );
};

export default SaleDetailsPage;
