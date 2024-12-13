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

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Flask for UTF-8
app.config['JSON_AS_ASCII'] = False

# Add encoding headers to all responses
@app.after_request
def add_header(response):
    if 'json' in response.content_type:
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

def json_response(data):
    """Helper function to create JSON responses with proper encoding"""
    response = jsonify(data)
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

# API configuration
CMC_API_KEY = os.getenv('CMC_API_KEY')
CMC_BASE_URL = 'https://pro-api.coinmarketcap.com/v1'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI client
proxy_str = os.getenv('PROXIES')
transport = httpx.HTTPTransport(
    proxy=Proxy(url=proxy_str) if proxy_str else None
)
http_client = httpx.Client(transport=transport, verify=False)
client = OpenAI(
    api_key=OPENAI_API_KEY,
    http_client=http_client
)

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

def load_prompt_template(filename):
    """Load prompt template from file"""
    try:
        with open(f'prompts/{filename}', 'r') as f:
            return f.read()
    except FileNotFoundError as e:
        print(f"Prompt template file not found: {filename} - {e}")
        return None
    except Exception as e:
        print(f"Error loading prompt template {filename}: {e}")
        return None

def get_crypto_prices(symbols):
    """Get current prices for cryptocurrencies"""
    try:
        headers = {
            'X-CMC_PRO_API_KEY': CMC_API_KEY,
        }
        
        # Handle USDB separately as it's a stablecoin pegged to USD
        if 'USDB' in symbols:
            symbols = [sym for sym in symbols if sym != 'USDB']
            
            # Create USDB data with fixed price of 1 USD converted to BRL
            # Get USD/BRL exchange rate using a regular USD-pegged stablecoin like USDT
            usdt_params = {
                'symbol': 'USDT',
                'convert': 'BRL'
            }
            usdt_response = requests.get(f'{CMC_BASE_URL}/cryptocurrency/quotes/latest', headers=headers, params=usdt_params)
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

def generate_market_analysis(portfolio_data: Dict, template_data: Dict) -> Dict:
    """
    Generate detailed portfolio analysis following 70-30 strategy
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
            'timestamp': datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
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

        # Calculate target values
        target_crypto_value = total_value * 0.7  # 70% target for crypto
        target_stable_value = total_value * 0.3  # 30% target for stable

        # Check if rebalancing is needed (5% threshold)
        if abs(current_crypto_pct - 70) > 5 or abs(current_stable_pct - 30) > 5:
            analysis_data['rebalance_needed'] = True

            # Calculate adjustments for each crypto asset
            crypto_assets = list(analysis_data['allocations']['crypto'].items())
            total_crypto_allocation = sum(data['allocation_total'] for _, data in crypto_assets)
            
            for symbol, data in crypto_assets:
                current_amount = data['amount']
                current_value = data['value_brl']
                price = data['price_brl']
                
                # Calculate target allocation within crypto portion (maintaining relative proportions)
                relative_weight = data['allocation_total'] / total_crypto_allocation if total_crypto_allocation > 0 else 0
                target_value = target_crypto_value * relative_weight
                target_amount = target_value / price if price > 0 else 0
                
                adjustment_amount = target_amount - current_amount
                adjustment_value = adjustment_amount * price
                
                analysis_data['asset_adjustments'].append({
                    'symbol': symbol,
                    'current_amount': current_amount,
                    'target_amount': target_amount,
                    'amount_adjustment': adjustment_amount,
                    'current_value_brl': current_value,
                    'target_value_brl': target_value,
                    'adjustment_brl': adjustment_value,
                    'action': 'comprar' if adjustment_amount > 0 else 'vender'
                })

            # Add rebalancing suggestions
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

        return analysis_data

    except Exception as e:
        print(f"Error in generate_market_analysis: {str(e)}")
        return {
            'error': str(e),
            'allocations': {'crypto': {}, 'stable': {}},
            'rebalance_suggestions': [],
            'asset_adjustments': []
        }

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

def format_stable_allocations(stable_data: Dict) -> str:
    """Format stablecoin allocation data for the prompt"""
    result = []
    for symbol, data in stable_data.items():
        result.append(f"- {symbol}:")
        result.append(f"  * Quantidade: {data['amount']:.8f}")
        result.append(f"  * Valor: R$ {data['value_brl']:.2f}")
        result.append(f"  * Alocação: {data['allocation_total']:.2f}%\n")
    return "\n".join(result)

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

def format_asset_adjustments(adjustments: List) -> str:
    """Format detailed asset-specific adjustments for the prompt"""
    if not adjustments:
        return ""

    result = ["\nAjustes Detalhados por Ativo:"]
    
    # Separate cryptos and stables for organized display
    stables = [adj for adj in adjustments if adj['symbol'] in ['USDT', 'MUSD', 'USDB']]
    cryptos = [adj for adj in adjustments if adj['symbol'] not in ['USDT', 'MUSD', 'USDB']]
    
    result.append("\nCriptomoedas:")
    for adj in cryptos:
        result.append(f"\n{adj['symbol']}:")
        result.append(f"  * Valor Atual: R$ {adj['current_value_brl']:.2f}")
        result.append(f"  * Valor Alvo: R$ {adj['target_value_brl']:.2f}")
        result.append(f"  * Quantidade Atual: {adj['current_amount']:.8f}")
        result.append(f"  * Quantidade Alvo: {adj['target_amount']:.8f}")
        result.append(f"  * Ajuste Necessário: {adj['action'].title()} {abs(adj['amount_adjustment']):.8f} unidades")
        result.append(f"  * Valor do Ajuste: R$ {abs(adj['adjustment_brl']):.2f}")

    if stables:
        result.append("\nStablecoins:")
        for adj in stables:
            result.append(f"\n{adj['symbol']}:")
            result.append(f"  * Valor Atual: R$ {adj['current_value_brl']:.2f}")
            result.append(f"  * Valor Alvo: R$ {adj['target_value_brl']:.2f}")
            result.append(f"  * Quantidade Atual: {adj['current_amount']:.8f}")
            result.append(f"  * Quantidade Alvo: {adj['target_amount']:.8f}")
            result.append(f"  * Ajuste Necessário: {adj['action'].title()} {abs(adj['amount_adjustment']):.8f} unidades")
            result.append(f"  * Valor do Ajuste: R$ {abs(adj['adjustment_brl']):.2f}")
    
    return "\n".join(result)

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

def save_portfolio(portfolio_data):
    """Save portfolio data to JSON file"""
    try:
        with open('portfolio.json', 'w') as f:
            json.dump(portfolio_data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving portfolio: {e}")
        return False

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

if __name__ == '__main__':
    app.run(debug=True)