import React, { useState } from 'react';
import axios from 'axios';

const AssetList = ({ assets, onUpdate, apiUrl }) => {
  const [editingAsset, setEditingAsset] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [error, setError] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

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
        setError('Por favor, insira um número positivo válido');
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
      setError(err.response?.data?.error || 'Falha ao atualizar o ativo');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleCancel = () => {
    setEditingAsset(null);
    setEditValue('');
    setError('');
  };

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const getSortedAssets = () => {
    const assetEntries = Object.entries(assets);
    if (!sortConfig.key) return assetEntries;

    return assetEntries.sort((a, b) => {
      let aValue, bValue;
      
      switch (sortConfig.key) {
        case 'symbol':
          [aValue, bValue] = [a[0], b[0]];
          break;
        case 'amount':
          [aValue, bValue] = [a[1].amount, b[1].amount];
          break;
        case 'price':
          [aValue, bValue] = [a[1].price_brl, b[1].price_brl];
          break;
        case 'value':
          [aValue, bValue] = [a[1].value_brl, b[1].value_brl];
          break;
        default:
          return 0;
      }

      if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  };

  const getFilteredAssets = () => {
    const sortedAssets = getSortedAssets();
    if (!searchTerm) return sortedAssets;

    return sortedAssets.filter(([symbol]) => 
      symbol.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  const getSortIcon = (key) => {
    if (sortConfig.key !== key) return '↕️';
    return sortConfig.direction === 'asc' ? '↑' : '↓';
  };

  return (
    <div className="asset-table-container">
      {error && <div className="error-message">{error}</div>}
      <div className="table-controls">
        <div className="search-container">
          <input
            type="text"
            placeholder="Buscar por símbolo..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>
      </div>
      <table className="asset-table">
        <thead>
          <tr>
            <th onClick={() => handleSort('symbol')} className="sortable-header">
              Ativo {getSortIcon('symbol')}
            </th>
            <th onClick={() => handleSort('amount')} className="sortable-header">
              Quantidade {getSortIcon('amount')}
            </th>
            <th onClick={() => handleSort('price')} className="sortable-header">
              Preço (BRL) {getSortIcon('price')}
            </th>
            <th onClick={() => handleSort('value')} className="sortable-header">
              Valor (BRL) {getSortIcon('value')}
            </th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          {getFilteredAssets().map(([symbol, asset]) => (
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
                      className="save-btn"
                      disabled={isUpdating}
                    >
                      {isUpdating ? 'Atualizando...' : 'Salvar'}
                    </button>
                    <button 
                      onClick={handleCancel} 
                      className="cancel-btn"
                      disabled={isUpdating}
                    >
                      Cancelar
                    </button>
                  </>
                ) : (
                  <button 
                    onClick={() => handleEdit(symbol, asset.amount)} 
                    className="edit-btn"
                    disabled={isUpdating}
                  >
                    Editar
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
