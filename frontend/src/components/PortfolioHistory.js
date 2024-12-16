import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './PortfolioHistory.css';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

// Use the same API URL configuration as App.js
const API_URL = process.env.NODE_ENV === 'production'
  ? 'https://portfolio-crypto-backend.onrender.com/api'
  : 'http://localhost:10000/api';

console.log('PortfolioHistory using API URL:', API_URL);

function PortfolioHistory() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await axios.get(`${API_URL}/portfolio/history`);
        console.log('History response:', response.data);
        
        if (response.data && Array.isArray(response.data.history)) {
          // Sort history by timestamp in ascending order for the chart
          const sortedHistory = response.data.history.sort((a, b) => 
            new Date(a.timestamp) - new Date(b.timestamp)
          );
          setHistory(sortedHistory);
        } else {
          console.error('Invalid history data format:', response.data);
          setError('Invalid history data format received');
        }
      } catch (err) {
        console.error('Error fetching history:', err);
        setError(err.message || 'Failed to load portfolio history');
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  const formatCurrency = (value) => {
    if (typeof value !== 'number') {
      console.warn('Invalid value for formatting:', value);
      return 'N/A';
    }
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatDate = (timestamp) => {
    if (!timestamp) {
      console.warn('Invalid timestamp:', timestamp);
      return 'N/A';
    }
    try {
      return new Date(timestamp).toLocaleString('pt-BR', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).replace('.', '');
    } catch (err) {
      console.error('Error formatting date:', err);
      return 'Invalid Date';
    }
  };

  const formatChartDate = (timestamp) => {
    try {
      return new Date(timestamp).toLocaleString('pt-BR', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
      }).replace('.', '');
    } catch (err) {
      return '';
    }
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="chart-tooltip">
          <p className="tooltip-date">{formatDate(label)}</p>
          <p className="tooltip-value">{formatCurrency(payload[0].value)}</p>
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return <div className="loading">Carregando histórico...</div>;
  }

  if (error) {
    return <div className="error">Erro: {error}</div>;
  }

  if (!history || history.length === 0) {
    return <div className="no-data">Nenhum histórico disponível.</div>;
  }

  return (
    <div className="portfolio-history">
      <h2>Histórico do Portfólio</h2>
      
      {/* Chart Section */}
      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={history}
            margin={{
              top: 10,
              right: 30,
              left: 20,
              bottom: 30
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis 
              dataKey="timestamp" 
              tickFormatter={formatChartDate}
              stroke="#8b8b8b"
              tick={{ fill: '#8b8b8b' }}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis 
              tickFormatter={(value) => formatCurrency(value)}
              stroke="#8b8b8b"
              tick={{ fill: '#8b8b8b' }}
              width={80}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line 
              type="monotone" 
              dataKey="value" 
              stroke="#00ff88" 
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6, fill: '#00ff88' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* List Section */}
      <div className="history-list">
        {[...history].reverse().map((entry, index) => (
          <div key={index} className="history-item">
            <div className="history-date">{formatDate(entry.timestamp)}</div>
            <div className="history-value">{formatCurrency(entry.value)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default PortfolioHistory;
