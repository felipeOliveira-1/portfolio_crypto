import React, { useState, useEffect } from 'react';
import axios from 'axios';
import PortfolioSummary from './components/PortfolioSummary';
import AssetList from './components/AssetList';
import PortfolioAnalysis from './components/PortfolioAnalysis';
import './App.css';

function App() {
  const [portfolioData, setPortfolioData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : true;
  });

  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
    document.body.classList.toggle('dark-mode', darkMode);
  }, [darkMode]);

  const fetchData = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/portfolio/analysis');
      setPortfolioData(response.data);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError(err.response?.data?.error || 'Failed to fetch portfolio data');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 300000);
    return () => clearInterval(interval);
  }, []);

  const handleRefreshAnalysis = async () => {
    setLoading(true);
    try {
      await fetchData();
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!portfolioData) return <div className="no-data">No portfolio data available</div>;

  return (
    <div className={`App ${darkMode ? 'dark-mode' : ''}`}>
      <header className="App-header">
        <h1>Crypto Portfolio</h1>
        <button 
          className="theme-toggle"
          onClick={() => setDarkMode(!darkMode)}
          aria-label="Toggle dark mode"
        >
          {darkMode ? '☀️' : '🌙'}
        </button>
      </header>
      <main>
        <div className="dashboard-container">
          <div className="summary-section">
            <PortfolioSummary data={portfolioData.portfolio} />
          </div>
          <div className="content-section">
            <div className="assets-section">
              <h2>Assets</h2>
              <AssetList 
                assets={portfolioData.portfolio.assets} 
                onUpdate={fetchData}
              />
            </div>
            <PortfolioAnalysis 
              portfolioData={portfolioData}
              onRefresh={handleRefreshAnalysis}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
