import React from 'react';
import PropTypes from 'prop-types';
import '../../styles/Button.css';

const Button = ({ 
  onClick, 
  children, 
  variant = 'primary', 
  size = 'medium',
  disabled = false,
  className = ''
}) => {
  return (
    <button
      className={`custom-button ${variant} ${size} ${className}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};

Button.propTypes = {
  onClick: PropTypes.func.isRequired,
  children: PropTypes.node.isRequired,
  variant: PropTypes.oneOf(['primary', 'secondary', 'danger']),
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  disabled: PropTypes.bool,
  className: PropTypes.string
};

export default Button;
