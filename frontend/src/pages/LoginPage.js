import React, { useState } from 'react';
import { Button, Spinner, Card, Form, Container, Row, Col } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import authService from '../services/authService';  // Use authService for login
import { isValidEmail } from '../utils/validators';  // Utility for email validation

function LoginPage({ onLogin, showToast }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleLogin = async () => {
    // Client-side validation before making the API request
    if (!email || !password) {
      showToast('warning', 'Please fill in all fields', 'Missing Fields');
      return;
    }

    if (!isValidEmail(email)) {
      showToast('warning', 'Please enter a valid email address', 'Invalid Email');
      return;
    }

    setLoading(true);

    try {
      // Use the authService to handle login
      const { access_token, refresh_token, user } = await authService.login({
        email,
        password,
      });

      // Store tokens and user info in localStorage for persistence
      localStorage.setItem('accessToken', access_token);  // Store access token
      localStorage.setItem('refreshToken', refresh_token);  // Store refresh token
      localStorage.setItem('userRole', user.role_id);  // Store user role
      localStorage.setItem('userID', user.id);         // Store user ID
      localStorage.setItem('user', JSON.stringify(user));  // Store user details

      // Call the onLogin function to set the role in the App state
      onLogin(user.role_id);

      // Show success toast
      showToast('success', 'Login successful!', 'Success');

      // Redirect to the appropriate page based on role immediately after successful login
      navigate(user.role_id == 3 ? '/manage-users' : '/sales');

    } catch (error) {
      setError(error.message || 'Login failed');
      showToast('danger', error.message || 'Login failed!', 'Error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container className="d-flex align-items-center justify-content-center vh-100">
      <Row className="justify-content-center">
        <Col>
          <Card className="p-4 shadow-sm">
            <Card.Body>
              <h2 className="text-center mb-4">Login</h2>
              <Form>
                <Form.Group controlId="formEmail" className="mb-3">
                  <Form.Label>Email address</Form.Label>
                  <Form.Control
                    type="email"
                    placeholder="Enter email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </Form.Group>

                <Form.Group controlId="formPassword" className="mb-3">
                  <Form.Label>Password</Form.Label>
                  <Form.Control
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </Form.Group>

                {error && <div className="text-danger text-center mb-3">{error}</div>}

                <div className="d-grid">
                  <Button variant="primary" size="lg" onClick={handleLogin} disabled={loading}>
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
