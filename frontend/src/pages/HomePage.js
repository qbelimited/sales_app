import React from 'react';
import { Card, Button, Container, Row, Col } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChartLine, faUsers, faFileAlt } from '@fortawesome/free-solid-svg-icons';

function HomePage() {
  const navigate = useNavigate();

  return (
    <Container className="mt-5">
      <h2 className="text-center mb-4">Sales Manager Dashboard</h2>
      <Row>
        {/* Sales Overview */}
        <Col md={4} className="mb-4">
          <Card className="shadow-sm h-100" style={{ transition: 'transform 0.2s', cursor: 'pointer' }} onClick={() => navigate('/sales')}>
            <Card.Body>
              <div className="d-flex align-items-center mb-3">
                <FontAwesomeIcon icon={faChartLine} size="2x" className="text-primary me-3" />
                <Card.Title>Total Sales</Card.Title>
              </div>
              <Card.Text>
                Overview of your total sales made this month.
              </Card.Text>
              <Button variant="primary" onClick={() => navigate('/sales')}>
                View Sales
              </Button>
            </Card.Body>
          </Card>
        </Col>

        {/* Manage Sales Executives */}
        <Col md={4} className="mb-4">
          <Card className="shadow-sm h-100" style={{ transition: 'transform 0.2s', cursor: 'pointer' }} onClick={() => navigate('/sales-executives')}>
            <Card.Body>
              <div className="d-flex align-items-center mb-3">
                <FontAwesomeIcon icon={faUsers} size="2x" className="text-success me-3" />
                <Card.Title>Manage Sales Executives</Card.Title>
              </div>
              <Card.Text>
                View and manage your team of sales executives.
              </Card.Text>
              <Button variant="success" onClick={() => navigate('/sales-executives')}>
                Manage Executives
              </Button>
            </Card.Body>
          </Card>
        </Col>

        {/* Reports */}
        <Col md={4} className="mb-4">
          <Card className="shadow-sm h-100" style={{ transition: 'transform 0.2s', cursor: 'pointer' }} onClick={() => navigate('/reports')}>
            <Card.Body>
              <div className="d-flex align-items-center mb-3">
                <FontAwesomeIcon icon={faFileAlt} size="2x" className="text-info me-3" />
                <Card.Title>Sales Reports</Card.Title>
              </div>
              <Card.Text>
                Generate and download sales reports for performance review.
              </Card.Text>
              <Button variant="info" onClick={() => navigate('/reports')}>
                View Reports
              </Button>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}

export default HomePage;
