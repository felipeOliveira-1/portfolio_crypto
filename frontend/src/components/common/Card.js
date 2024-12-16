import React from 'react';
import PropTypes from 'prop-types';
import '../../styles/Card.css';

const Card = ({ 
  children, 
  title, 
  className = '', 
  headerAction,
  variant = 'default'
}) => {
  return (
    <div className={`custom-card ${variant} ${className}`}>
      {title && (
        <div className="card-header">
          <h3 className="card-title">{title}</h3>
          {headerAction && (
            <div className="card-header-action">
              {headerAction}
            </div>
          )}
        </div>
      )}
      <div className="card-content">
        {children}
      </div>
    </div>
  );
};

Card.propTypes = {
  children: PropTypes.node.isRequired,
  title: PropTypes.string,
  className: PropTypes.string,
  headerAction: PropTypes.node,
  variant: PropTypes.oneOf(['default', 'outlined', 'elevated'])
};

export default Card;
