import './app.scss';

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Homepage from './pages/homepage/Homepage';
import Dashboard from './pages/dashboard/Dashboard';
import About from './pages/about/About';
import Contact from './pages/contact/Contact';
import NoPage from "./pages/NoPage";
import Navbar from './components/navbar/Navbar';

const App = () => {
  return (
    <BrowserRouter>
      <Navbar/> {/* Navbar should now appear on all pages */}
      <Routes>
        <Route path="/" element={<Homepage />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/about" element={<About />} />
        <Route path="/contact" element={<Contact />} />
        <Route path="*" element={<NoPage />} /> {/* Handle undefined routes */}
      </Routes>
    </BrowserRouter>
  );
}

export default App;
