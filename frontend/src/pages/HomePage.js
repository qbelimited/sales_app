import React from 'react';
import { Card, Button, Container, Row, Col } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';

function HomePage() {
  const navigate = useNavigate();

  return (
    <Container className="mt-5">
      <h2 className="text-center mb-4">Sales Manager Dashboard</h2>
      <Row>
        {/* Sales Overview */}
        <Col md={4} className="mb-4">
          <Card className="shadow-sm">
            <Card.Body>
              <Card.Title>Total Sales</Card.Title>
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
          <Card className="shadow-sm">
            <Card.Body>
              <Card.Title>Manage Sales Executives</Card.Title>
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
          <Card className="shadow-sm">
            <Card.Body>
              <Card.Title>Sales Reports</Card.Title>
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
