import React from 'react';
import { Link } from 'react-router-dom';
import { Container, Row, Col, Button } from 'react-bootstrap';
import './UnauthorizedPage.css'; // Make sure to create this CSS file for custom styling

const UnauthorizedPage = () => {
  return (
    <Container className="d-flex justify-content-center align-items-center min-vh-100">
      <Row className="text-center">
        <Col>
          <div className="unauthorized-message">
            <h1 className="display-4">Unauthorized</h1>
            <p className="lead">
              You do not have permission to view this page.
            </p>
            <Link to="/login">
              <Button variant="primary">Go back to Login</Button>
            </Link>
          </div>
        </Col>
      </Row>
    </Container>
  );
};

export default UnauthorizedPage;
