import React, { useState } from 'react';
import { Container, TextField, Button, Typography, Box, Paper } from '@mui/material';
import { GoogleLogin } from '@react-oauth/google';
import { jwtDecode } from 'jwt-decode';
import { useNavigate } from 'react-router-dom';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();  // ✅ Now it's inside the function

  const handleLogin = (e) => {
    e.preventDefault();
    console.log('Login attempt:', { email, password });
  };

  const handleSuccess = (credentialResponse) => {
    const credential = credentialResponse.credential;
    console.log("credential", credential)
    const decoded = jwtDecode(credential);
    console.log('Decoded Google token:', decoded);

    fetch('http://127.0.0.1:8000/api/v1/users/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id_token: credential }),
    })
      .then((res) => res.json())
      .then((data) => {
        console.log('Backend response:', data);
        // Example: Save token if needed
        // localStorage.setItem('token', data.accessToken);
        navigate('/'); // ✅ Navigate to home on success
      })
      .catch((err) => console.error('Error sending token:', err));
  };

  return (
    <Container maxWidth="sm">
      <Paper elevation={3} sx={{ padding: 4, marginTop: 10 }}>
        <Typography variant="h5" align="center" gutterBottom>
          Login to VideoTube
        </Typography>

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

        <Typography align="center" variant="body2" sx={{ mt: 2 }}>
          Don't have an account?{' '}
          <a href="/signup" style={{ color: '#1976d2', textDecoration: 'none' }}>
            Sign up
          </a>
        </Typography>

        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <GoogleLogin
            onSuccess={handleSuccess}
            onError={() => console.log('Google login failed')}
          />
        </Box>
      </Paper>
    </Container>
  );
}
