import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const PortfolioSummary = ({ data }) => {
  if (!data || !data.total_brl) return null;

  const { total_brl, assets } = data;
  
  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#6366f1', '#ec4899', '#8b5cf6'];

  const allocation = Object.entries(assets).map(([symbol, asset]) => ({
    symbol,
    value: asset.value_brl / total_brl,
    percentage: ((asset.value_brl / total_brl) * 100).toFixed(2)
  }));

  // Calcular variações (exemplo com dados simulados - você precisará adicionar estes dados no backend)
  const change24h = 5.32; // Exemplo: +5.32%
  const change7d = -2.15; // Exemplo: -2.15%

  const formatPercentage = (value) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  const getPercentageClass = (value) => {
    return value >= 0 ? 'percentage-positive' : 'percentage-negative';
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload[0]) {
      const data = payload[0].payload;
      return (
        <div style={{
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          padding: '8px',
          borderRadius: '4px',
          color: 'white',
          fontSize: '14px'
        }}>
          <div>{data.symbol}</div>
          <div>{data.percentage}%</div>
        </div>
      );
    }
    return null;
  };

  return (
    <>
      <div className="total-value-container">
        <div className="total-value-label">Total Portfolio Value</div>
        <div className="total-value">
          R$ {Number(total_brl).toFixed(2)}
        </div>
        <div className="portfolio-metrics">
          <div className="metric">
            <span className="metric-label">24h</span>
            <span className={getPercentageClass(change24h)}>
              {formatPercentage(change24h)}
            </span>
          </div>
          <div className="metric">
            <span className="metric-label">7d</span>
            <span className={getPercentageClass(change7d)}>
              {formatPercentage(change7d)}
            </span>
          </div>
        </div>
      </div>

      <div className="assets-grid">
        {Object.entries(assets).map(([symbol, asset]) => (
          <div key={symbol} className="asset-card">
            <div className="asset-symbol">{symbol}</div>
            <div className="asset-amount">{Number(asset.amount).toFixed(8)}</div>
            <div className="asset-value">R$ {Number(asset.value_brl).toFixed(2)}</div>
          </div>
        ))}
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={allocation}
              cx="50%"
              cy="50%"
              labelLine={false}
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
            >
              {allocation.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
        <div className="chart-legend">
          {allocation.map((item, index) => (
            <div key={index} className="legend-item">
              <span className="legend-color" style={{ backgroundColor: COLORS[index % COLORS.length] }}></span>
              <span className="legend-label">{item.symbol}</span>
              <span className="legend-value">{item.percentage}%</span>
            </div>
          ))}
        </div>
      </div>
    </>
  );
};

export default PortfolioSummary;
