// App.jsx
import { BrowserRouter as Router } from 'react-router-dom';
import AppRoutes from "./routes/Routes.jsx";


export default function App() {
  return (
    <Router>
      {/* Can add global context providers here if needed */}
      <AppRoutes />
    </Router>
  );
}
