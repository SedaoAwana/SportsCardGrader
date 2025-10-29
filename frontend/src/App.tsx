import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { HomePage, AboutPage, DebugPage } from './components/pages';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/debug" element={<DebugPage />} />
      </Routes>
    </Router>
  );
}

export default App;
