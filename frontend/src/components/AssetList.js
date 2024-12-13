import React, { useState } from 'react';
import axios from 'axios';

const AssetList = ({ assets, onUpdate, apiUrl }) => {
  const [editingAsset, setEditingAsset] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [error, setError] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);

  const formatBRL = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatAmount = (value) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 8,
      maximumFractionDigits: 8
    }).format(value);
  };

  const handleEdit = (symbol, amount) => {
    setEditingAsset(symbol);
    setEditValue(amount.toString());
    setError('');
  };

  const handleSave = async (symbol) => {
    try {
      const newAmount = parseFloat(editValue);
      if (isNaN(newAmount) || newAmount < 0) {
        setError('Please enter a valid positive number');
        return;
      }

      setIsUpdating(true);
      setError('');

      const response = await axios.post(`${apiUrl}/portfolio/update`, {
        assets: {
          [symbol]: newAmount
        }
      });

      if (response.data.message === 'Portfolio updated successfully') {
        setEditingAsset(null);
        if (onUpdate) await onUpdate();
      }
    } catch (err) {
      console.error('Error updating asset:', err);
      setError(err.response?.data?.error || 'Failed to update asset');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleCancel = () => {
    setEditingAsset(null);
    setEditValue('');
    setError('');
  };

  return (
    <div className="asset-table-container">
      {error && <div className="error-message">{error}</div>}
      <table className="asset-table">
        <thead>
          <tr>
            <th>Asset</th>
            <th>Amount</th>
            <th>Price (BRL)</th>
            <th>Value (BRL)</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(assets).map(([symbol, asset]) => (
            <tr key={symbol} className={isUpdating && editingAsset === symbol ? 'updating' : ''}>
              <td className="asset-symbol-cell">{symbol}</td>
              <td className="asset-amount-cell">
                {editingAsset === symbol ? (
                  <input
                    type="text"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    className="amount-input"
                    autoFocus
                    disabled={isUpdating}
                  />
                ) : (
                  formatAmount(asset.amount)
                )}
              </td>
              <td className="asset-price-cell">{formatBRL(asset.price_brl)}</td>
              <td className="asset-value-cell">{formatBRL(asset.value_brl)}</td>
              <td className="asset-actions-cell">
                {editingAsset === symbol ? (
                  <>
                    <button 
                      onClick={() => handleSave(symbol)} 
                      className={`save-btn ${isUpdating ? 'updating' : ''}`}
                      disabled={isUpdating}
                    >
                      {isUpdating ? 'Updating...' : 'Save'}
                    </button>
                    <button 
                      onClick={handleCancel} 
                      className="cancel-btn"
                      disabled={isUpdating}
                    >
                      Cancel
                    </button>
                  </>
                ) : (
                  <button 
                    onClick={() => handleEdit(symbol, asset.amount)} 
                    className="edit-btn"
                    disabled={isUpdating}
                  >
                    Edit
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default AssetList;
