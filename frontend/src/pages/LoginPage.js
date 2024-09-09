import React, { useState } from 'react';
import { Button, Spinner, Card, Form, Container, Row, Col } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Toaster from '../components/Toaster';

function LoginPage({ onLogin }) {
  const [toasts, setToasts] = useState([]);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  const showToast = (variant, message, heading) => {
    const newToast = {
      id: Date.now(),
      variant,
      message,
      heading,
      time: new Date(),
    };
    setToasts((prevToasts) => [...prevToasts, newToast]);
  };

  const handleLogin = async () => {
    setLoading(true);

    try {
      const response = await axios.post('http://127.0.0.1:5000/api/v1/auth/login', {
        email,
        password,
      });

      if (response.status === 200) {
        const { access_token, refresh_token, user } = response.data;

        // Store the tokens and user information in localStorage
        localStorage.setItem('accessToken', access_token);
        localStorage.setItem('refreshToken', refresh_token);
        localStorage.setItem('userRole', user.role_id);  // Store the role ID for role-based access
        localStorage.setItem('userID', user.id);  // Store the user ID
        localStorage.setItem('user', JSON.stringify(user));  // Store the full user object for later use if needed

        // Call the onLogin function to set the role in the App state
        onLogin(user.role_id);  // Pass the role ID to the parent App component

        // Redirect to the home page
        navigate('/home');

        showToast('success', 'Login successful!', 'Success');
      }
    } catch (error) {
      showToast('danger', error.response?.data?.message || 'Login failed!', 'Error');
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

      <Toaster toasts={toasts} removeToast={(id) => setToasts(toasts.filter((t) => t.id !== id))} />
    </Container>
  );
}

export default LoginPage;
