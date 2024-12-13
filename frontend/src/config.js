const config = {
    API_URL: process.env.REACT_APP_API_URL || (
        process.env.NODE_ENV === 'production'
            ? 'https://portfolio-crypto-backend.onrender.com/api'
            : 'http://localhost:5000/api'
    )
};

export default config;
