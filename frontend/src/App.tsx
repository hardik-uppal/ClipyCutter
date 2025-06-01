import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import InputScreen from './screens/InputScreen';
import PreviewScreen from './screens/PreviewScreen';
import UploadScreen from './screens/UploadScreen';
import './App.css';

function App() {
  return (
    <div className="App">
      <Router>
        <header className="App-header">
          <h1>🎬 Clippy v2</h1>
          <p>Create viral YouTube shorts from any video</p>
        </header>
        
        <main className="App-main">
          <Routes>
            <Route path="/" element={<InputScreen />} />
            <Route path="/preview/:clipId" element={<PreviewScreen />} />
            <Route path="/upload/:clipId" element={<UploadScreen />} />
          </Routes>
        </main>
      </Router>
    </div>
  );
}

export default App;