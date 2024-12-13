import React, { useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const PortfolioSummary = ({ data }) => {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'ascending' });
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);

  React.useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  if (!data || !data.total_brl) return null;

  const { total_brl, assets, changes } = data;
  
  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#6366f1', '#ec4899', '#8b5cf6'];

  const formatPercentage = (value) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${Number(value).toFixed(2)}%`;
  };

  const getPercentageClass = (value) => {
    return value >= 0 ? 'percentage-positive' : 'percentage-negative';
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  // Prepare data for table
  const tableData = Object.entries(assets).map(([symbol, asset]) => {
    const weight = (asset.value_brl / total_brl) * 100;
    return {
      symbol,
      amount: asset.amount,
      price_brl: asset.price_brl,
      value_brl: asset.value_brl,
      weight: weight,
      change_24h: asset.percent_change_24h,
    };
  });

  // Sorting function
  const sortData = (key) => {
    setSortConfig((current) => {
      const direction = current.key === key && current.direction === 'ascending' ? 'descending' : 'ascending';
      return { key, direction };
    });
  };

  // Apply sorting
  const sortedData = [...tableData].sort((a, b) => {
    if (!sortConfig.key) return 0;
    
    const direction = sortConfig.direction === 'ascending' ? 1 : -1;
    return a[sortConfig.key] > b[sortConfig.key] ? direction : -direction;
  });

  // Prepare data for pie chart
  const pieData = sortedData.map(asset => ({
    name: asset.symbol,
    value: asset.weight,
  }));

  return (
    <div className="portfolio-container">
      <div className="portfolio-metrics">
        <div className="metric-card">
          <div className="metric-header">
            <h3>Total do Portfólio</h3>
          </div>
          <div className="metric-body">
            <p className="metric-value">{formatCurrency(total_brl)}</p>
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-header">
            <h3>Variação 24h</h3>
          </div>
          <div className="metric-body">
            <p className={`metric-value ${getPercentageClass(changes?.change_24h || 0)}`}>
              {formatPercentage(changes?.change_24h || 0)}
            </p>
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
              formatter={(value) => formatCurrency(value)}
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
              <th onClick={() => sortData('symbol')}>Ativo</th>
              <th onClick={() => sortData('amount')}>Quantidade</th>
              {!isMobile && (
                <>
                  <th onClick={() => sortData('price_brl')}>Preço (BRL)</th>
                  <th onClick={() => sortData('value_brl')}>Valor Total</th>
                </>
              )}
              <th onClick={() => sortData('weight')}>Peso</th>
              <th onClick={() => sortData('change_24h')}>24h</th>
            </tr>
          </thead>
          <tbody>
            {sortedData.map((item) => (
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
                <td className={getPercentageClass(item.change_24h)}>
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
