import React from 'react';
import './LoadingSpinner.css';

const LoadingSpinner = () => {
  return (
    <div className="loading-container">
      <div className="crypto-spinner">
        <div className="coin">
          <div className="front"></div>
          <div className="back"></div>
          <div className="side">
            {[...Array(20)].map((_, i) => (
              <div key={i} style={{ '--i': i }}></div>
            ))}
          </div>
        </div>
      </div>
      <div className="loading-text">
        <span>L</span>
        <span>o</span>
        <span>a</span>
        <span>d</span>
        <span>i</span>
        <span>n</span>
        <span>g</span>
        <span>.</span>
        <span>.</span>
        <span>.</span>
      </div>
    </div>
  );
};

export default LoadingSpinner;
