import React, { useState, useCallback } from 'react';
import { Button, Spinner, Card, Form, Container, Row, Col } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import authService from '../services/authService';  // Use authService for login
import { isValidEmail } from '../utils/validators';  // Utility for email validation

function LoginPage({ onLogin, showToast }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [emailError, setEmailError] = useState(null);
  const [passwordError, setPasswordError] = useState(null);
  const [formError, setFormError] = useState(null);
  const navigate = useNavigate();

  // Handle login logic with error handling
  const handleLogin = useCallback(async () => {
    // Reset specific errors
    setEmailError(null);
    setPasswordError(null);
    setFormError(null);

    // Client-side validation before making the API request
    if (!email) {
      setEmailError('Email is required.');
      return;
    }

    if (!isValidEmail(email)) {
      setEmailError('Please provide a valid email address.');
      return;
    }

    if (!password) {
      setPasswordError('Password is required.');
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
      navigate(user.role_id === 3 ? '/manage-users' : '/sales');
    } catch (error) {
      // Handle errors from the API
      setFormError(error.response?.data?.message || 'Login failed');
      showToast('danger', error.response?.data?.message || 'Login failed!', 'Error');
    } finally {
      setLoading(false);
    }
  }, [email, password, onLogin, showToast, navigate]);

  // Handle form submission
  const handleSubmit = useCallback(
    (e) => {
      e.preventDefault();
      handleLogin();
    },
    [handleLogin]
  );

  return (
    <Container className="d-flex align-items-center justify-content-center vh-100">
      <Row className="justify-content-center">
        <Col md={6} lg={12}>
          <Card className="p-4 shadow-sm">
            <Card.Body>
              <h2 className="text-center mb-4">Login</h2>
              <Form onSubmit={handleSubmit}>
                <Form.Group controlId="formEmail" className="mb-3">
                  <Form.Label>Email address</Form.Label>
                  <Form.Control
                    type="email"
                    placeholder="Enter email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    isInvalid={!!emailError}
                    required
                  />
                  <Form.Control.Feedback type="invalid">
                    {emailError}
                  </Form.Control.Feedback>
                </Form.Group>

                <Form.Group controlId="formPassword" className="mb-3">
                  <Form.Label>Password</Form.Label>
                  <Form.Control
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    isInvalid={!!passwordError}
                    required
                  />
                  <Form.Control.Feedback type="invalid">
                    {passwordError}
                  </Form.Control.Feedback>
                </Form.Group>

                {formError && (
                  <div className="text-danger text-center mb-3">{formError}</div>
                )}

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
