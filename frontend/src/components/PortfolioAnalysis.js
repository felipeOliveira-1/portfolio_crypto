import React from 'react';

const PortfolioAnalysis = ({ portfolioData, onRefresh }) => {
  // Return null if portfolio data is not provided or doesn't have the expected structure
  if (!portfolioData || !portfolioData.analysis || !portfolioData.timestamp) {
    return null;
  }

  // Format the analysis text by removing XML tags and cleaning up the content
  const formatAnalysis = (analysisText) => {
    try {
      return analysisText
        .replace(/```xml/g, '')  // Remove ```xml
        .replace(/```/g, '')     // Remove remaining ```
        .replace(/<\?xml[^>]*\?>/g, '')  // Remove XML declaration
        .replace(/<[^>]*>/g, '')         // Remove all XML tags
        .replace(/\*\*/g, '')            // Remove asterisks
        .split('\n')                     // Split into lines
        .map(line => line.trim())        // Trim whitespace
        .filter(line => line)            // Remove empty lines
        .join('\n');                     // Join back with newlines
    } catch (error) {
      console.error('Error formatting analysis:', error);
      return analysisText; // Return original text if formatting fails
    }
  };

  const formattedAnalysis = formatAnalysis(portfolioData.analysis);

  return (
    <div className="analysis-section">
      <div className="analysis-header">
        <h2>Portfolio Analysis</h2>
        <button 
          className="refresh-button"
          onClick={onRefresh}
        >
          Atualizar Análise
        </button>
      </div>
      <div className="timestamp">
        Analysis generated at: {portfolioData.timestamp}
      </div>
      <div className="analysis-content">
        <div className="analysis-text">
          {formattedAnalysis.split('\n').map((paragraph, index) => (
            paragraph ? <p key={index}>{paragraph}</p> : null
          ))}
        </div>
      </div>
    </div>
  );
};

export default PortfolioAnalysis;
