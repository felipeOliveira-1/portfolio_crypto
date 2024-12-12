import React from 'react';

const PortfolioAnalysis = ({ portfolioData }) => {
  // Return null if portfolio data is not provided or doesn't have the expected structure
  if (!portfolioData || !portfolioData.analysis || !portfolioData.timestamp) {
    return null;
  }

  // Format the analysis text by removing XML tags and cleaning up the content
  const formatAnalysis = (analysisText) => {
    return analysisText
      .replace(/```xml/g, '')  // Remove ```xml
      .replace(/```/g, '')     // Remove remaining ```
      .replace(/<\?xml[^>]*\?>/g, '')  // Remove XML declaration
      .replace(/<[^>]*>/g, '')         // Remove all XML tags
      .split('\n')                     // Split into lines
      .map(line => line.trim())        // Trim whitespace
      .filter(line => line)            // Remove empty lines
      .join('\n');                     // Join back with newlines
  };

  const formattedAnalysis = formatAnalysis(portfolioData.analysis);

  return (
    <div className="analysis-section">
      <h2>Portfolio Analysis</h2>
      <div className="timestamp">
        Analysis generated at: {new Date(portfolioData.timestamp).toLocaleString('pt-BR')}
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
