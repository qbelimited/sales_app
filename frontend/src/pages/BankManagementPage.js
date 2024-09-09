import React from 'react';
import { Card, CardContent, Typography, Button } from '@mui/material';
import { Container, Row, Col } from 'react-bootstrap';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';

const BankManagementPage = () => {
  return (
    <Container className="mt-4">
      <Row>
        <Col md={12}>
          <Typography variant="h4" gutterBottom>
            Bank and Branch Management
          </Typography>
        </Col>
      </Row>
      <Row>
        <Col md={4}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="div">
                Add Bank
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Create a new bank and its branches.
              </Typography>
              <Button
                variant="contained"
                color="primary"
                startIcon={<AddIcon />}
                className="mt-3"
              >
                Add New Bank
              </Button>
            </CardContent>
          </Card>
        </Col>
        <Col md={4}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="div">
                Edit Bank
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Edit existing bank information.
              </Typography>
              <Button
                variant="contained"
                color="secondary"
                startIcon={<EditIcon />}
                className="mt-3"
              >
                Edit Bank
              </Button>
            </CardContent>
          </Card>
        </Col>
        <Col md={4}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="div">
                View Branches
              </Typography>
              <Typography variant="body2" color="text.secondary">
                View and manage branches under each bank.
              </Typography>
              <Button
                variant="contained"
                color="info"
                startIcon={<EditIcon />}
                className="mt-3"
              >
                View Branches
              </Button>
            </CardContent>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default BankManagementPage;
