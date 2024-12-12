# Portfolio Crypto

Um aplicativo web para gerenciar e analisar um portfólio de criptomoedas, com valores atualizados em tempo real.

## Funcionalidades

- Visualização de ativos em tempo real com preços em BRL
- Edição de quantidades de ativos
- Análise de portfólio usando IA
- Suporte a múltiplas criptomoedas incluindo stablecoins (USDB)
- Interface responsiva e amigável

## Tecnologias Utilizadas

### Backend
- Python
- Flask
- CoinMarketCap API
- OpenAI API

### Frontend
- React
- JavaScript
- CSS

## Configuração

1. Clone o repositório:
```bash
git clone https://github.com/felipeOliveira-1/portfolio_crypto.git
```

2. Configure as variáveis de ambiente:
Crie um arquivo `.env` no diretório backend com:
```
CMC_API_KEY=sua_chave_api_coinmarketcap
OPENAI_API_KEY=sua_chave_api_openai
```

3. Instale as dependências do backend:
```bash
cd backend
pip install -r requirements.txt
```

4. Instale as dependências do frontend:
```bash
cd frontend
npm install
```

5. Execute o backend:
```bash
cd backend
python app.py
```

6. Execute o frontend:
```bash
cd frontend
npm start
```

## Estrutura do Projeto

```
portfolio_crypto/
├── backend/
│   ├── app.py
│   ├── portfolio.json
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/
    │   ├── App.js
    │   └── App.css
    └── package.json
```
