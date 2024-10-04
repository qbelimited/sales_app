import React, { useState } from 'react';
import { Button, Spinner, Card, Form, Container, Row, Col } from 'react-bootstrap';
import { isValidEmail } from '../utils/validators'; // Utility for email validation
import useAuth from '../hooks/useAuth'; // Import the custom hook

function LoginPage({ showToast }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { handleLogin } = useAuth(); // Use handleLogin from useAuth

  const onSubmit = async (e) => {
    e.preventDefault();
    setError(null); // Clear previous errors

    // Client-side validation
    if (!email || !password) {
      setError('Please fill in all fields');
      showToast('warning', 'Please fill in all fields', 'Missing Fields');
      return;
    }

    if (!isValidEmail(email)) {
      setError('Please enter a valid email address');
      showToast('warning', 'Please enter a valid email address', 'Invalid Email');
      return;
    }

    setLoading(true);

    try {
      await handleLogin({ email, password }); // Try logging in with provided credentials
      showToast('success', 'Login successful!', 'Success');
    } catch (error) {
      // Catch network or authentication errors
      console.error('Login error:', error);
      setError(error?.message || 'Login failed. Please try again.');
      showToast('danger', error?.message || 'Login failed!', 'Error');
    } finally {
      setLoading(false); // Stop the loading spinner after the process finishes
    }
  };

  return (
    <Container className="d-flex align-items-center justify-content-center vh-100">
      <Row className="justify-content-center">
        <Col>
          <Card className="p-4 shadow-sm">
            <Card.Body>
              <h2 className="text-center mb-4">Login</h2>
              <Form onSubmit={onSubmit}>
                <Form.Group controlId="formEmail" className="mb-3">
                  <Form.Label>Email address</Form.Label>
                  <Form.Control
                    type="email"
                    placeholder="Enter email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    isInvalid={!!error && !isValidEmail(email)}
                    required
                  />
                  <Form.Control.Feedback type="invalid">
                    {error && !isValidEmail(email) ? error : 'Please enter a valid email.'}
                  </Form.Control.Feedback>
                </Form.Group>

                <Form.Group controlId="formPassword" className="mb-3">
                  <Form.Label>Password</Form.Label>
                  <Form.Control
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    isInvalid={!!error && isValidEmail(email)}
                    required
                  />
                  <Form.Control.Feedback type="invalid">
                    {error && isValidEmail(email) ? error : 'Incorrect password.'}
                  </Form.Control.Feedback>
                </Form.Group>

                {error && <div className="text-danger text-center mb-3">{error}</div>}

                <div className="d-grid">
                  <Button variant="primary" size="lg" type="submit" disabled={loading}>
                    {loading ? <Spinner animation="border" size="sm" /> : 'Login'}
                  </Button>
                </div>
              </Form>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}

export default LoginPage;
