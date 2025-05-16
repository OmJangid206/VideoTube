import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { GoogleOAuthProvider } from '@react-oauth/google'

import App from './App.jsx'
import './index.css'


const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
if (!clientId) throw new Error("Missing Google OAuth client ID")
  
const root = createRoot(document.getElementById('root'))
root.render(
  <StrictMode>
    <GoogleOAuthProvider clientId={clientId}>
      <App />
    </GoogleOAuthProvider>
  </StrictMode>
)
