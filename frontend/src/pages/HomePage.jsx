// src/pages/HomePage.jsx
import React from 'react';
import { Typography, Container } from '@mui/material';

export default function HomePage() {
  return (
    <Container sx={{ mt: 10 }}>
      <Typography variant="h4">Welcome to VideoTube 🎬</Typography>
    </Container>
  );
}