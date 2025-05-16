import React, { useState } from 'react';
import { Container, TextField, Button, Typography, Box, Paper, Alert } from '@mui/material';
import { GoogleLogin } from '@react-oauth/google';
import { jwtDecode } from 'jwt-decode';
import { useNavigate } from 'react-router-dom';

const BACKEND_BASE_URL = import.meta.env.VITE_BACKEND_BASE_URL;

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    console.log('Email/password login attempt:', { email, password });

    // TODO: Implement traditional login if needed
    setError('Email/password login is not implemented yet.');
  };

  const handleGoogleLoginSuccess = async (credentialResponse) => {
    try {
      setError('');
      setSuccess('');

      const credential = credentialResponse.credential;
      const decodedToken = jwtDecode(credential);

      console.log('Google login success. Decoded token:', decodedToken);

      const response = await fetch(`${BACKEND_BASE_URL}/api/v1/users/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id_token: credential }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Google login failed');
      }

      setSuccess('Login successful. Redirecting...');
      // Optionally save tokens: localStorage.setItem('token', data.accessToken);
      setTimeout(() => navigate('/'), 1000);
    } catch (err) {
      console.error('Login error:', err);
      setError(err.message || 'An unexpected error occurred.');
    }
  };

  const handleGoogleLoginError = () => {
    setError('Google login failed. Please try again.');
    setSuccess('');
  };

  return (
    <Container maxWidth="sm">
      <Paper elevation={3} sx={{ padding: 4, marginTop: 10 }}>
        <Typography variant="h5" align="center" gutterBottom>
          Sign in to VideoTube
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
        {success && (
          <Alert severity="success" sx={{ mt: 2 }}>
            {success}
          </Alert>
        )}

        <Box component="form" onSubmit={handleLogin} sx={{ mt: 2 }}>
          <TextField
            fullWidth
            label="Email"
            type="email"
            margin="normal"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <TextField
            fullWidth
            label="Password"
            type="password"
            margin="normal"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button
            fullWidth
            type="submit"
            variant="contained"
            color="primary"
            sx={{ mt: 3 }}
          >
            Log In
          </Button>
        </Box>
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <GoogleLogin
            onSuccess={handleGoogleLoginSuccess}
            onError={handleGoogleLoginError}
          />
        </Box>
        <Typography align="center" variant="body2" sx={{ mt: 2 }}>
          Don&apos;t have an account?{' '}
          <a href="/signup" style={{ color: '#1976d2', textDecoration: 'none' }}>
            Sign up
          </a>
        </Typography>
      </Paper>
    </Container>
  );
}
