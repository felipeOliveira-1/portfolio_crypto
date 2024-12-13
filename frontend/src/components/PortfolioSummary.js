import React, { useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const PortfolioSummary = ({ data }) => {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'ascending' });

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
      change_7d: asset.percent_change_7d,
      market_cap: data.market_data?.[symbol]?.market_cap,
      volume_24h: data.market_data?.[symbol]?.volume_24h
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

  // Format numbers
  const formatNumber = (number, decimals = 2) => {
    if (number >= 1e9) return `${(number / 1e9).toFixed(decimals)}B`;
    if (number >= 1e6) return `${(number / 1e6).toFixed(decimals)}M`;
    if (number >= 1e3) return `${(number / 1e3).toFixed(decimals)}K`;
    return number.toFixed(decimals);
  };

  // Prepare data for pie chart
  const chartData = sortedData.map(asset => ({
    symbol: asset.symbol,
    value: asset.weight,
    amount: formatNumber(asset.amount, 8),
    valueFormatted: `R$ ${formatNumber(asset.value_brl)}`
  }));

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload[0]) {
      const data = payload[0].payload;
      return (
        <div className="chart-tooltip">
          <div className="tooltip-symbol">{data.symbol}</div>
          <div className="tooltip-value">{data.valueFormatted}</div>
          <div className="tooltip-amount">{data.amount} {data.symbol}</div>
          <div className="tooltip-weight">{data.value.toFixed(2)}% do portfólio</div>
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
            <span className={getPercentageClass(changes?.change_24h || 0)}>
              {formatPercentage(changes?.change_24h || 0)}
            </span>
          </div>
          <div className="metric">
            <span className="metric-label">7d</span>
            <span className={getPercentageClass(changes?.change_7d || 0)}>
              {formatPercentage(changes?.change_7d || 0)}
            </span>
          </div>
        </div>
      </div>

      <div className="assets-table-container">
        <table className="assets-table">
          <thead>
            <tr>
              <th onClick={() => sortData('symbol')}>Asset</th>
              <th onClick={() => sortData('amount')}>Amount</th>
              <th onClick={() => sortData('price_brl')}>Price (BRL)</th>
              <th onClick={() => sortData('value_brl')}>Value (BRL)</th>
              <th onClick={() => sortData('weight')}>Weight</th>
              <th onClick={() => sortData('change_24h')}>24h Change</th>
              <th onClick={() => sortData('change_7d')}>7d Change</th>
              <th onClick={() => sortData('market_cap')}>Market Cap</th>
              <th onClick={() => sortData('volume_24h')}>24h Volume</th>
            </tr>
          </thead>
          <tbody>
            {sortedData.map((asset) => (
              <tr key={asset.symbol}>
                <td>
                  <div className="asset-symbol-container">
                    <img 
                      src={`https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/32/color/${asset.symbol.toLowerCase()}.png`} 
                      alt={asset.symbol}
                      onError={(e) => e.target.style.display = 'none'}
                    />
                    {asset.symbol}
                  </div>
                </td>
                <td className="amount-column">{formatNumber(asset.amount, 8)}</td>
                <td className="price-column">R$ {formatNumber(asset.price_brl)}</td>
                <td className="value-column">R$ {formatNumber(asset.value_brl)}</td>
                <td className="value-column">{asset.weight.toFixed(2)}%</td>
                <td className={`value-column ${getPercentageClass(asset.change_24h)}`}>
                  {formatPercentage(asset.change_24h)}
                </td>
                <td className={`value-column ${getPercentageClass(asset.change_7d)}`}>
                  {formatPercentage(asset.change_7d)}
                </td>
                <td className="value-column">R$ {formatNumber(asset.market_cap)}</td>
                <td className="value-column">R$ {formatNumber(asset.volume_24h)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="symbol"
              cx="50%"
              cy="50%"
              outerRadius={100}
              labelLine={false}
              animationBegin={0}
              animationDuration={1500}
            >
              {chartData.map((entry, index) => (
                <Cell key={entry.symbol} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              formatter={(value, entry) => `${value} (${entry.payload.value.toFixed(2)}%)`}
              layout="vertical"
              align="right"
              verticalAlign="middle"
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </>
  );
};

export default PortfolioSummary;
