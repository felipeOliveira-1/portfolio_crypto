const API_PORT = 10000;

const config = {
    API_URL: process.env.REACT_APP_API_URL || (
        process.env.NODE_ENV === 'production'
            ? 'https://portfolio-crypto-backend.onrender.com/api'
            : `http://localhost:${API_PORT}/api`
    )
};

console.log('Config API_URL:', config.API_URL);

export default config;
