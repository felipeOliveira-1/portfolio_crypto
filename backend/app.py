from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI
import datetime
import httpx
from httpx import Proxy
import traceback
from typing import Dict, List
import threading
from datetime import datetime, timedelta, timezone

# Load environment variables
load_dotenv()

# API configuration with defaults
CMC_BASE_URL = 'https://pro-api.coinmarketcap.com/v1'  # Default URL
CMC_API_KEY = os.getenv('CMC_API_KEY', '')  # Your API key from .env
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')  # Your OpenAI key from .env

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "https://portfolio-crypto-frontend.onrender.com"]}})

# Configure Flask for UTF-8
app.config['JSON_AS_ASCII'] = False
app.config['DEBUG'] = True  # Enable debug mode

def add_header(response):
    """Add CORS headers to response"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

def json_response(data):
    """Helper function to create JSON responses with proper encoding"""
    response = jsonify(data)
    return add_header(response)

# Global lock for file operations
portfolio_lock = threading.Lock()

# Configuration constants
MAX_HISTORY_ENTRIES = 1000  # Maximum number of history entries to keep
MAX_HISTORY_AGE_DAYS = 90   # Maximum age of history entries in days
HISTORY_FILE_PATH = os.path.join('data', 'portfolio_history.json')

# Load prompt templates
def load_prompt_template(filename):
    """Load prompt template from file"""
    try:
        with open(f'prompts/{filename}', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError as e:
        print(f"Prompt template file not found: {filename} - {e}")
        return None
    except Exception as e:
        print(f"Error loading prompt template {filename}: {e}")
        return None

# Initialize OpenAI client
def init_openai_client():
    """Initialize OpenAI client with proxy"""
    proxy_str = os.getenv('PROXIES')
    transport = httpx.HTTPTransport(
        proxy=Proxy(url=proxy_str) if proxy_str else None
    )
    http_client = httpx.Client(transport=transport, verify=False)
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        http_client=http_client
    )
    return client

# Load portfolio data from JSON file
def load_portfolio():
    """Load portfolio data from JSON file"""
    try:
        with open('portfolio.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError as e:
        print(f"Portfolio file not found: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing portfolio.json: {e}")
        return {}
    except Exception as e:
        print(f"Unexpected error loading portfolio: {e}")
        return {}

# Get current prices for cryptocurrencies
def get_crypto_prices(symbols):
    """Get current prices for cryptocurrencies"""
    try:
        # Set up headers with API key
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': CMC_API_KEY,
        }
        
        # Handle USDB separately as it's a stablecoin pegged to USD
        prices = {}
        if 'USDB' in symbols:
            usdt_params = {
                'symbol': 'USDT',
                'convert': 'BRL'
            }
            usdt_response = requests.get(f'{CMC_BASE_URL}/cryptocurrency/quotes/latest', headers=headers, params=usdt_params)
            
            # Create USDB data with fixed price of 1 USD converted to BRL
            # Get USD/BRL exchange rate using a regular USD-pegged stablecoin like USDT
            usdt_data = usdt_response.json()
            
            if usdt_response.status_code == 200 and 'data' in usdt_data:
                usdt_price_brl = usdt_data['data']['USDT']['quote']['BRL']['price']
                # Create synthetic USDB data using USDT's BRL price
                data = {
                    'USDB': {
                        'symbol': 'USDB',
                        'name': 'USD Balance',
                        'quote': {
                            'BRL': {
                                'price': usdt_price_brl,
                                'percent_change_24h': 0,  # Stablecoin, so no change
                                'percent_change_7d': 0,
                                'market_cap': 0,
                                'volume_24h': 0
                            }
                        }
                    }
                }
            else:
                print(f"Error fetching USDT price for USDB conversion: {usdt_data.get('status', {}).get('error_message')}")
                return None
            
            # Then get other crypto prices
            if symbols:
                params = {
                    'symbol': ','.join(symbols),
                    'convert': 'BRL'
                }
                crypto_response = requests.get(f'{CMC_BASE_URL}/cryptocurrency/quotes/latest', headers=headers, params=params)
                crypto_data = crypto_response.json()
                
                if crypto_response.status_code == 200 and 'data' in crypto_data:
                    data.update(crypto_data['data'])
                else:
                    print(f"Error fetching crypto prices: {crypto_data.get('status', {}).get('error_message')}")
                    return None
                    
            return data
        else:
            # If no USDB, just get regular crypto prices
            params = {
                'symbol': ','.join(symbols),
                'convert': 'BRL'
            }
            response = requests.get(f'{CMC_BASE_URL}/cryptocurrency/quotes/latest', headers=headers, params=params)
            data = response.json()
            
            if response.status_code == 200 and 'data' in data:
                return data['data']
            else:
                print(f"Error fetching prices: {data.get('status', {}).get('error_message')}")
                return None
            
    except Exception as e:
        print(f"Error in get_crypto_prices: {e}\n{traceback.format_exc()}")
        return None

# Get price changes for cryptocurrencies from CoinMarketCap
def get_crypto_price_changes(symbols: List[str]) -> Dict:
    """
    Get price changes for cryptocurrencies from CoinMarketCap
    Args:
        symbols: List of cryptocurrency symbols
    Returns:
        Dict containing price changes for each symbol
    """
    try:
        # Convert symbols to CMC format
        symbols_str = ','.join(symbols)
        
        url = f"{CMC_BASE_URL}/cryptocurrency/quotes/latest"
        parameters = {
            'symbol': symbols_str,
            'convert': 'BRL'
        }
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': CMC_API_KEY
        }

        response = requests.get(url, headers=headers, params=parameters)
        data = response.json()

        if 'data' not in data:
            print(f"Error getting price changes: {data.get('status', {}).get('error_message', 'Unknown error')}")
            return {}

        changes = {}
        for symbol in symbols:
            if symbol in data['data']:
                quote = data['data'][symbol]['quote']['BRL']
                changes[symbol] = {
                    'change_24h': quote['percent_change_24h'],
                    'change_7d': quote['percent_change_7d']
                }
            else:
                changes[symbol] = {
                    'change_24h': 0,
                    'change_7d': 0
                }

        return changes

    except Exception as e:
        print(f"Error getting price changes: {str(e)}")
        traceback.print_exc()
        return {}

# Calculate portfolio value changes based on individual asset changes
def calculate_portfolio_changes(portfolio_data: Dict) -> Dict:
    """
    Calculate portfolio value changes based on individual asset changes
    Args:
        portfolio_data: Dictionary containing portfolio information
    Returns:
        Dict containing portfolio changes
    """
    try:
        assets = portfolio_data.get('assets', {})
        if not assets:
            return {'change_24h': 0, 'change_7d': 0}

        # Get symbols
        symbols = list(assets.keys())
        
        # Get price changes from CMC
        price_changes = get_crypto_price_changes(symbols)
        
        # Calculate weighted changes
        total_value = portfolio_data['total_brl']
        weighted_24h = 0
        weighted_7d = 0

        for symbol, asset in assets.items():
            # Calculate weight of this asset in portfolio
            weight = asset['value_brl'] / total_value
            
            # Get asset changes
            asset_changes = price_changes.get(symbol, {'change_24h': 0, 'change_7d': 0})
            
            # Add weighted changes
            weighted_24h += weight * asset_changes['change_24h']
            weighted_7d += weight * asset_changes['change_7d']

        return {
            'change_24h': weighted_24h,
            'change_7d': weighted_7d
        }

    except Exception as e:
        print(f"Error calculating portfolio changes: {str(e)}")
        traceback.print_exc()
        return {'change_24h': 0, 'change_7d': 0}

# Generate detailed portfolio analysis following 70-30 strategy with 2.5% tolerance
def generate_market_analysis(portfolio_data: Dict, template_data: Dict) -> Dict:
    """
    Generate detailed portfolio analysis following 70-30 strategy with 2.5% tolerance
    Args:
        portfolio_data: Dictionary containing portfolio information
        template_data: Dictionary containing analysis templates
    Returns:
        Dict containing detailed analysis
    """
    try:
        # Initialize analysis data
        analysis_data = {
            'total_value_brl': portfolio_data['total_brl'],
            'timestamp': datetime.now(timezone(timedelta(hours=-3))).isoformat(),
            'allocations': {'crypto': {}, 'stable': {}},
            'rebalance_needed': False,
            'rebalance_suggestions': [],
            'asset_adjustments': []  # List for detailed asset adjustments
        }

        # Separate assets into crypto and stablecoins
        stablecoins = ['USDT', 'MUSD', 'USDB']
        crypto_value = 0
        stable_value = 0

        # Calculate current allocations and store prices
        for symbol, data in portfolio_data['assets'].items():
            is_stable = symbol in stablecoins
            value_brl = data['value_brl']
            current_price = data['price_brl']
            
            asset_data = {
                'amount': data['amount'],
                'value_brl': value_brl,
                'allocation_total': (value_brl / analysis_data['total_value_brl']) * 100,
                'price_brl': current_price
            }

            if is_stable:
                stable_value += value_brl
                analysis_data['allocations']['stable'][symbol] = asset_data
            else:
                crypto_value += value_brl
                asset_data.update({
                    'price_change_24h': data.get('percent_change_24h', 0),
                    'price_change_7d': data.get('percent_change_7d', 0)
                })
                analysis_data['allocations']['crypto'][symbol] = asset_data

        total_value = analysis_data['total_value_brl']
        current_crypto_pct = (crypto_value / total_value) * 100
        current_stable_pct = (stable_value / total_value) * 100

        # Check if portfolio is within 70-30 tolerance (±2.5%)
        THRESHOLD = 2.5
        if abs(current_crypto_pct - 70) > THRESHOLD:  # Only rebalance if portfolio is out of range
            analysis_data['rebalance_needed'] = True
            
            # Calculate target values
            target_crypto_value = total_value * 0.7  # 70% target for crypto
            target_stable_value = total_value * 0.3  # 30% target for stable

            # Add portfolio-level rebalancing suggestions
            analysis_data['rebalance_suggestions'].append({
                'type': 'crypto',
                'current_percentage': current_crypto_pct,
                'target_percentage': 70,
                'adjustment_brl': target_crypto_value - crypto_value
            })
            analysis_data['rebalance_suggestions'].append({
                'type': 'stable',
                'current_percentage': current_stable_pct,
                'target_percentage': 30,
                'adjustment_brl': target_stable_value - stable_value
            })

            # Calculate adjustments for each asset to achieve target allocation
            crypto_assets = list(analysis_data['allocations']['crypto'].items())
            total_crypto_allocation = sum(data['allocation_total'] for _, data in crypto_assets)
            
            # Adjust cryptos proportionally
            for symbol, data in crypto_assets:
                current_amount = data['amount']
                current_value = data['value_brl']
                price = data['price_brl']
                
                # Maintain relative weights within crypto portion
                relative_weight = data['allocation_total'] / total_crypto_allocation if total_crypto_allocation > 0 else 0
                target_value = target_crypto_value * relative_weight
                target_amount = target_value / price if price > 0 else 0
                
                adjustment_amount = target_amount - current_amount
                adjustment_value = adjustment_amount * price
                
                current_pct = (current_value / total_value) * 100
                target_pct = (target_value / total_value) * 100

                analysis_data['asset_adjustments'].append({
                    'symbol': symbol,
                    'current_amount': current_amount,
                    'target_amount': target_amount,
                    'amount_adjustment': adjustment_amount,
                    'current_value_brl': current_value,
                    'target_value_brl': target_value,
                    'adjustment_brl': adjustment_value,
                    'current_percentage': current_pct,
                    'target_percentage': target_pct,
                    'action': 'comprar' if adjustment_amount > 0 else 'vender'
                })

            # Adjust stablecoins proportionally
            stable_assets = list(analysis_data['allocations']['stable'].items())
            total_stable_allocation = sum(data['allocation_total'] for _, data in stable_assets)
            
            for symbol, data in stable_assets:
                current_amount = data['amount']
                current_value = data['value_brl']
                price = data['price_brl']
                
                relative_weight = data['allocation_total'] / total_stable_allocation if total_stable_allocation > 0 else 0
                target_value = target_stable_value * relative_weight
                target_amount = target_value / price if price > 0 else 0
                
                adjustment_amount = target_amount - current_amount
                adjustment_value = adjustment_amount * price
                
                current_pct = (current_value / total_value) * 100
                target_pct = (target_value / total_value) * 100

                analysis_data['asset_adjustments'].append({
                    'symbol': symbol,
                    'current_amount': current_amount,
                    'target_amount': target_amount,
                    'amount_adjustment': adjustment_amount,
                    'current_value_brl': current_value,
                    'target_value_brl': target_value,
                    'adjustment_brl': adjustment_value,
                    'current_percentage': current_pct,
                    'target_percentage': target_pct,
                    'action': 'comprar' if adjustment_amount > 0 else 'vender'
                })

        return analysis_data

    except Exception as e:
        print(f"Error in generate_market_analysis: {str(e)}")
        return {
            'error': str(e),
            'allocations': {'crypto': {}, 'stable': {}},
            'rebalance_suggestions': [],
            'asset_adjustments': []
        }

# Format cryptocurrency allocation data for the prompt
def format_crypto_allocations(crypto_data: Dict) -> str:
    """Format cryptocurrency allocation data for the prompt"""
    result = []
    for symbol, data in crypto_data.items():
        result.append(f"- {symbol}:")
        result.append(f"  * Quantidade: {data['amount']:.8f}")
        result.append(f"  * Valor: R$ {data['value_brl']:.2f}")
        result.append(f"  * Alocação Total: {data['allocation_total']:.2f}%")
        result.append(f"  * Alocação Relativa (70%): {data.get('allocation_relative', 0):.2f}%")
        result.append(f"  * Variação 24h: {data['price_change_24h']:.2f}%")
        result.append(f"  * Variação 7d: {data['price_change_7d']:.2f}%\n")
    return "\n".join(result)

# Format stablecoin allocation data for the prompt
def format_stable_allocations(stable_data: Dict) -> str:
    """Format stablecoin allocation data for the prompt"""
    result = []
    for symbol, data in stable_data.items():
        result.append(f"- {symbol}:")
        result.append(f"  * Quantidade: {data['amount']:.8f}")
        result.append(f"  * Valor: R$ {data['value_brl']:.2f}")
        result.append(f"  * Alocação: {data['allocation_total']:.2f}%\n")
    return "\n".join(result)

# Format rebalancing suggestions for the prompt
def format_rebalancing_suggestions(suggestions: List) -> str:
    """Format rebalancing suggestions for the prompt"""
    result = ["Ajustes Recomendados por Categoria:"]
    for suggestion in suggestions:
        action = "Aumentar" if suggestion['adjustment_brl'] > 0 else "Reduzir"
        result.append(f"- {suggestion['type'].title()}:")
        result.append(f"  * Atual: {suggestion['current_percentage']:.2f}%")
        result.append(f"  * Alvo: {suggestion['target_percentage']:.2f}%")
        result.append(f"  * Ação: {action} exposição em R$ {abs(suggestion['adjustment_brl']):.2f}\n")
    return "\n".join(result)

# Format detailed asset-specific adjustments for the prompt
def format_asset_adjustments(adjustments: List) -> str:
    """Format detailed asset-specific adjustments for the prompt"""
    if not adjustments:
        return "\nPortfólio está dentro da margem de tolerância de ±2.5% da regra 70-30. Não são necessários ajustes no momento."

    result = ["\nRecomendações de Rebalanceamento (Portfólio fora da margem 70-30 ±2.5%):"]
    
    # Separate cryptos and stables
    cryptos = [adj for adj in adjustments if adj['symbol'] not in ['USDT', 'MUSD', 'USDB']]
    stables = [adj for adj in adjustments if adj['symbol'] in ['USDT', 'MUSD', 'USDB']]
    
    if cryptos:
        result.append("\n1. Ajustes em Criptomoedas:")
        for adj in cryptos:
            action = "COMPRAR" if adj['amount_adjustment'] > 0 else "VENDER"
            result.append(f"\n{adj['symbol']} - {action}:")
            result.append(f"  * Alocação atual: {adj['current_percentage']:.2f}% do portfólio total")
            result.append(f"  * Nova alocação: {adj['target_percentage']:.2f}% do portfólio total")
            result.append(f"  * Quantidade exata: {abs(adj['amount_adjustment']):.8f} {adj['symbol']}")
            result.append(f"  * Valor em R$: {abs(adj['adjustment_brl']):.2f}")
            result.append(f"  * Quantidade atual: {adj['current_amount']:.8f} {adj['symbol']}")
            result.append(f"  * Quantidade após ajuste: {adj['target_amount']:.8f} {adj['symbol']}")
    
    if stables:
        result.append("\n2. Ajustes em Stablecoins:")
        for adj in stables:
            action = "COMPRAR" if adj['amount_adjustment'] > 0 else "VENDER"
            result.append(f"\n{adj['symbol']} - {action}:")
            result.append(f"  * Alocação atual: {adj['current_percentage']:.2f}% do portfólio total")
            result.append(f"  * Nova alocação: {adj['target_percentage']:.2f}% do portfólio total")
            result.append(f"  * Quantidade exata: {abs(adj['amount_adjustment']):.8f} {adj['symbol']}")
            result.append(f"  * Valor em R$: {abs(adj['adjustment_brl']):.2f}")
            result.append(f"  * Quantidade atual: {adj['current_amount']:.8f} {adj['symbol']}")
            result.append(f"  * Quantidade após ajuste: {adj['target_amount']:.8f} {adj['symbol']}")
    
    result.append("\nObservações Importantes:")
    result.append("1. Estas recomendações visam reequilibrar o portfólio para a regra 70-30")
    result.append("2. Os ajustes são necessários pois o portfólio está fora da margem de tolerância de ±2.5%")
    result.append("3. As proporções entre ativos da mesma categoria (cripto/stable) são mantidas")
    result.append("4. Execute as ordens na sequência sugerida para manter o balanceamento correto")
    result.append("5. Os valores em R$ são aproximados e podem variar devido à volatilidade do mercado")
    
    return "\n".join(result)

# Get AI analysis of the portfolio
def get_ai_analysis(portfolio_data: Dict) -> Dict:
    """Get AI analysis of the portfolio"""
    try:
        # Load prompt templates
        system_prompt = load_prompt_template('system_prompt_pt.xml')
        user_prompt_template = load_prompt_template('user_prompt_template_pt.xml')

        if not system_prompt or not user_prompt_template:
            return {"error": "Failed to load prompt templates"}

        # Generate detailed market analysis
        template_data = {
            'system_prompt': system_prompt,
            'user_template': user_prompt_template
        }
        
        analysis_data = generate_market_analysis(portfolio_data, template_data)
        if not analysis_data:
            return {"error": "Failed to generate market analysis"}

        # Format analysis prompt
        user_prompt = f"""
Análise de Portfólio - {analysis_data['timestamp']}

Status atual do portfólio:
- Valor Total: R$ {analysis_data['total_value_brl']:.2f}

Alocação por Categoria:
Criptomoedas (Alvo: 70%):
{format_crypto_allocations(analysis_data['allocations']['crypto'])}

Stablecoins (Alvo: 30%):
{format_stable_allocations(analysis_data['allocations']['stable'])}

Necessidade de Rebalanceamento:
{format_rebalancing_suggestions(analysis_data['rebalance_suggestions']) if analysis_data['rebalance_needed'] else 'Portfólio dentro dos limites de tolerância (±2.5%)'}

{format_asset_adjustments(analysis_data['asset_adjustments'])}
"""

        # Get AI analysis with specific parameters
        client = init_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.13,
            max_tokens=1500,
            presence_penalty=0.3,
            frequency_penalty=0.3
        )

        # Extract and clean the analysis
        analysis = response.choices[0].message.content.strip()
        analysis = analysis.encode('utf-8').decode('utf-8')

        return {
            "analysis": analysis,
            "timestamp": analysis_data['timestamp'],
            "metrics": analysis_data
        }

    except Exception as e:
        error_msg = f"Error in AI analysis: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return {"error": str(e)}

# Clean old history entries from portfolio history
def clean_old_history(history_data):
    """Remove old entries from history based on configured limits"""
    if not history_data or "history" not in history_data:
        return {"history": []}

    history = history_data["history"]
    
    # Sort by timestamp (newest first)
    history.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Keep only MAX_HISTORY_ENTRIES
    history = history[:MAX_HISTORY_ENTRIES]
    
    # Remove entries older than MAX_HISTORY_AGE_DAYS
    cutoff_date = (datetime.now(timezone(timedelta(hours=-3))) - timedelta(days=MAX_HISTORY_AGE_DAYS)).isoformat()
    history = [entry for entry in history if entry["timestamp"] >= cutoff_date]
    
    return {"history": history}

# Save portfolio data and append changes to history with concurrency control
def save_portfolio_with_history(portfolio_data):
    """Save portfolio data and append changes to history with concurrency control"""
    with portfolio_lock:  # Use lock to prevent concurrent file access
        try:
            # Load current history
            if os.path.exists(HISTORY_FILE_PATH):
                with open(HISTORY_FILE_PATH, 'r') as f:
                    history_data = json.load(f)
            else:
                history_data = {"history": []}
            
            # Get current prices for portfolio valuation
            symbols = list(portfolio_data.keys())
            prices = get_crypto_prices(symbols)
            
            # Calculate total portfolio value
            total_value = 0
            for symbol, quantity in portfolio_data.items():
                if symbol in prices:
                    price_brl = prices[symbol]['quote']['BRL']['price']
                    value_brl = float(quantity) * price_brl
                    total_value += value_brl
            
            # Add new state to history
            history_data["history"].append({
                "timestamp": datetime.now(timezone(timedelta(hours=-3))).isoformat(),
                "value": total_value
            })
            
            # Clean old history entries
            history_data = clean_old_history(history_data)

            # Ensure data directory exists
            os.makedirs(os.path.dirname(HISTORY_FILE_PATH), exist_ok=True)

            # Save updated history
            with open(HISTORY_FILE_PATH, 'w') as f:
                json.dump(history_data, f, indent=4)

            # Save the updated portfolio
            with open('portfolio.json', 'w') as f:
                json.dump(portfolio_data, f, indent=4)

            return True
        except Exception as e:
            print(f"Error saving portfolio with history: {e}")
            return False

# Save portfolio data to JSON file with history tracking
def save_portfolio(portfolio_data):
    """Save portfolio data to JSON file with history tracking"""
    try:
        return save_portfolio_with_history(portfolio_data)
    except Exception as e:
        print(f"Error saving portfolio: {e}")
        return False

# Get portfolio with current values in BRL
@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get portfolio with current values in BRL"""
    portfolio = load_portfolio()
    
    if not portfolio:
        return json_response({'error': 'Portfolio not found'}), 404
    
    prices = get_crypto_prices(list(portfolio.keys()))
    
    if not prices:
        return json_response({'error': 'Unable to fetch current prices'}), 500
    
    portfolio_data = {
        'assets': {},
        'total_brl': 0
    }
    
    for symbol, amount in portfolio.items():
        if symbol in prices:
            price_brl = prices[symbol]['quote']['BRL']['price']
            value_brl = float(amount) * price_brl
            
            portfolio_data['assets'][symbol] = {
                'amount': amount,
                'price_brl': price_brl,
                'value_brl': value_brl
            }
            
            portfolio_data['total_brl'] += value_brl
    
    return json_response(portfolio_data)

# Update portfolio asset quantities
@app.route('/api/portfolio/update', methods=['POST'])
def update_portfolio():
    """Update portfolio asset quantities"""
    try:
        data = request.get_json()
        if not data or 'assets' not in data:
            return json_response({'error': 'Invalid request data'}), 400

        # Load current portfolio
        current_portfolio = load_portfolio()
        if not current_portfolio:
            return json_response({'error': 'Failed to load current portfolio'}), 500

        # Update quantities
        for symbol, amount in data['assets'].items():
            try:
                current_portfolio[symbol] = float(amount)
            except (ValueError, TypeError) as e:
                return json_response({'error': f'Invalid amount for {symbol}: {str(e)}'}), 400

        # Save updated portfolio
        if save_portfolio(current_portfolio):
            return json_response({'message': 'Portfolio updated successfully', 'portfolio': current_portfolio})
        else:
            return json_response({'error': 'Failed to save portfolio'}), 500

    except Exception as e:
        error_msg = f"Error updating portfolio: {str(e)}"
        print(error_msg)
        return json_response({'error': error_msg}), 500

# Get portfolio with AI analysis
@app.route('/api/portfolio/analysis', methods=['GET'])
def get_portfolio_analysis():
    """Get portfolio with AI analysis"""
    try:
        portfolio = load_portfolio()
        if not portfolio:
            print("No portfolio data found")
            return json_response({'error': 'Portfolio not found'}), 404
        
        print(f"Portfolio loaded: {portfolio}")
        
        prices = get_crypto_prices(list(portfolio.keys()))
        if not prices:
            print("Failed to fetch crypto prices")
            return json_response({'error': 'Unable to fetch current prices'}), 500
        
        print(f"Prices fetched successfully")
        
        portfolio_data = {
            'assets': {},
            'total_brl': 0,
            'market_data': {}
        }
        
        for symbol, amount in portfolio.items():
            if symbol in prices:
                crypto_data = prices[symbol]
                try:
                    price_brl = crypto_data['quote']['BRL']['price']
                    if price_brl is None:
                        print(f"No price available for {symbol}")
                        continue
                        
                    value_brl = float(amount) * price_brl
                    
                    portfolio_data['assets'][symbol] = {
                        'amount': amount,
                        'price_brl': price_brl,
                        'value_brl': value_brl,
                        'percent_change_24h': crypto_data['quote']['BRL'].get('percent_change_24h', 0),
                        'percent_change_7d': crypto_data['quote']['BRL'].get('percent_change_7d', 0)
                    }
                    
                    portfolio_data['total_brl'] += value_brl
                    
                    portfolio_data['market_data'][symbol] = {
                        'price_change_24h': crypto_data['quote']['BRL'].get('percent_change_24h', 0),
                        'price_change_7d': crypto_data['quote']['BRL'].get('percent_change_7d', 0),
                        'market_cap': crypto_data['quote']['BRL'].get('market_cap', 0),
                        'volume_24h': crypto_data['quote']['BRL'].get('volume_24h', 0)
                    }
                except (KeyError, TypeError) as e:
                    print(f"Error processing data for {symbol}: {str(e)}")
                    continue
        
        print(f"Portfolio data processed: {portfolio_data}")

        # Calculate portfolio changes using CMC data
        changes = calculate_portfolio_changes(portfolio_data)
        portfolio_data["changes"] = changes

        # Get AI analysis
        analysis_result = get_ai_analysis(portfolio_data)
        
        if 'error' in analysis_result:
            print(f"Error in AI analysis: {analysis_result['error']}")
            return json_response({'error': analysis_result['error']}), 500
        
        print("Analysis completed successfully")
        
        return json_response({
            'portfolio': portfolio_data,
            'analysis': analysis_result['analysis'],
            'timestamp': analysis_result['timestamp'],
            'metrics': analysis_result['metrics']
        })
        
    except Exception as e:
        error_msg = f"Error in portfolio analysis: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return json_response({'error': str(e)}), 500

# Get portfolio history with optional time filter
@app.route('/api/portfolio/history')
def get_portfolio_history_endpoint():
    """Get portfolio history with optional time filter"""
    print("Received request for portfolio history")  # Debug log
    try:
        # Get days parameter from query string, default to None (all history)
        days = request.args.get('days', type=int)
        print(f"Filtering history for days: {days}")  # Debug log
        
        history_data = get_portfolio_history(days)
        print(f"Returning history data: {history_data}")  # Debug log
        
        return json_response(history_data)
    except Exception as e:
        error_msg = f"Error retrieving portfolio history: {str(e)}"
        print(f"Error in history endpoint: {error_msg}")  # Debug log
        traceback.print_exc()  # Print full traceback
        return json_response({"error": error_msg}), 500

# Retrieve portfolio history with optional time filter
def get_portfolio_history(days=None):
    """Retrieve portfolio history with optional time filter"""
    try:
        if not os.path.exists(HISTORY_FILE_PATH):
            print(f"History file not found at: {HISTORY_FILE_PATH}")
            return {"history": []}
        
        with open(HISTORY_FILE_PATH, 'r') as f:
            history_data = json.load(f)
            print(f"Loaded history data: {history_data}")  # Debug log
        
        if days is not None:
            cutoff_date = (datetime.now(timezone(timedelta(hours=-3))) - timedelta(days=days)).isoformat()
            history_data["history"] = [
                entry for entry in history_data["history"]
                if entry["timestamp"] >= cutoff_date
            ]
        
        return history_data
    except Exception as e:
        print(f"Error retrieving portfolio history: {e}")
        traceback.print_exc()
        return {"history": []}

# Register routes at the end of the file
@app.route('/')
def home():
    return "Portfolio Crypto API"

if __name__ == '__main__':
    print("Starting Flask server...")
    print(f"Available routes: {[str(rule) for rule in app.url_map.iter_rules()]}")  # Debug log
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
