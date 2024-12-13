import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const PortfolioSummary = ({ data }) => {
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  if (!data || !data.total_brl) return null;

  const { total_brl, assets, changes } = data;
  
  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#6366f1', '#ec4899', '#8b5cf6'];

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatPercentage = (value) => {
    if (value === undefined || value === null) return '0.00%';
    return `${value > 0 ? '+' : ''}${Number(value).toFixed(2)}%`;
  };

  const getVariationClass = (value) => {
    if (value === undefined || value === null) return '';
    return Number(value) >= 0 ? 'percentage-positive' : 'percentage-negative';
  };

  // Prepare data for pie chart
  const pieData = Object.entries(assets).map(([symbol, asset]) => ({
    name: symbol,
    value: (asset.value_brl / total_brl) * 100,
  }));

  // Prepare data for table
  const tableData = Object.entries(assets).map(([symbol, asset]) => ({
    symbol,
    amount: asset.amount,
    price_brl: asset.price_brl,
    value_brl: asset.value_brl,
    weight: (asset.value_brl / total_brl) * 100,
    change_24h: asset.percent_change_24h,
  }));

  return (
    <div className="portfolio-container">
      <div className="portfolio-metrics">
        <div className="metric-card">
          <h3>Total do Portfólio</h3>
          <div className="metric-value">{formatCurrency(total_brl)}</div>
          <div className="variations">
            <div className="variation">
              <span className="variation-label">24h:</span>
              <span className={getVariationClass(changes?.change_24h)}>
                {formatPercentage(changes?.change_24h)}
              </span>
            </div>
            <div className="variation">
              <span className="variation-label">7d:</span>
              <span className={getVariationClass(changes?.change_7d)}>
                {formatPercentage(changes?.change_7d)}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              innerRadius={isMobile ? "45%" : "50%"}
              outerRadius={isMobile ? "70%" : "80%"}
              paddingAngle={2}
              dataKey="value"
            >
              {pieData.map((entry, index) => (
                <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value) => `${value.toFixed(2)}%`}
              contentStyle={{
                backgroundColor: 'var(--bg-secondary)',
                border: '1px solid var(--border-color)',
                borderRadius: '0.5rem',
                color: 'var(--text-primary)'
              }}
            />
            <Legend
              verticalAlign={isMobile ? "bottom" : "middle"}
              align={isMobile ? "center" : "right"}
              layout={isMobile ? "horizontal" : "vertical"}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="table-container">
        <table className="portfolio-table">
          <thead>
            <tr>
              <th>Ativo</th>
              <th>Quantidade</th>
              {!isMobile && (
                <>
                  <th>Preço (BRL)</th>
                  <th>Valor Total</th>
                </>
              )}
              <th>Peso</th>
              <th>24h</th>
            </tr>
          </thead>
          <tbody>
            {tableData.map((item) => (
              <tr key={item.symbol}>
                <td className="asset-symbol-cell">{item.symbol}</td>
                <td>{Number(item.amount).toFixed(8)}</td>
                {!isMobile && (
                  <>
                    <td>{formatCurrency(item.price_brl)}</td>
                    <td>{formatCurrency(item.value_brl)}</td>
                  </>
                )}
                <td>{item.weight.toFixed(2)}%</td>
                <td className={getVariationClass(item.change_24h)}>
                  {formatPercentage(item.change_24h)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PortfolioSummary;
