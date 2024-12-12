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
from typing import Dict

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

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

def get_ai_analysis(portfolio_data: Dict) -> Dict:
    """Get AI analysis of the portfolio"""
    try:
        # Load prompt templates
        system_prompt = load_prompt_template('system_prompt_pt.xml')
        user_prompt_template = load_prompt_template('user_prompt_template_pt.xml')

        if not system_prompt or not user_prompt_template:
            return {"error": "Failed to load prompt templates"}

        # Format user prompt with current data
        current_time = datetime.datetime.now().isoformat()
        
        # Calculate portfolio allocations
        total_value = portfolio_data['total_brl']
        assets = portfolio_data['assets']
        
        # Separate stablecoins and crypto
        stablecoins = {symbol: data for symbol, data in assets.items() if symbol in ['USDT', 'USDB']}
        cryptos = {symbol: data for symbol, data in assets.items() if symbol not in ['USDT', 'USDB']}
        
        current_stable_value = sum(data['value_brl'] for data in stablecoins.values())
        current_crypto_value = sum(data['value_brl'] for data in cryptos.values())
        
        # Calculate target values
        target_crypto_value = total_value * 0.70
        target_stable_value = total_value * 0.30
        
        # Format detailed portfolio analysis
        holdings_text = "DETALHAMENTO DOS ATIVOS:\n"
        
        # Add cryptocurrencies details
        holdings_text += "\nCRYPTOCURRENCIES:\n"
        for symbol, data in sorted(cryptos.items(), key=lambda x: x[1]['value_brl'], reverse=True):
            allocation_pct = (data['value_brl'] / total_value) * 100
            relative_crypto_pct = (data['value_brl'] / current_crypto_value * 100) if current_crypto_value > 0 else 0
            
            holdings_text += f"- {symbol}:\n"
            holdings_text += f"  * Quantidade: {data['amount']:.8f}\n"
            holdings_text += f"  * Valor: R$ {data['value_brl']:.2f}\n"
            holdings_text += f"  * Alocação Total: {allocation_pct:.1f}%\n"
            holdings_text += f"  * Alocação Relativa (dentro dos 70%): {relative_crypto_pct:.1f}%\n"
            holdings_text += f"  * Variação 24h: {data['percent_change_24h']:.2f}%\n"
            holdings_text += f"  * Variação 7d: {data['percent_change_7d']:.2f}%\n\n"
        
        # Add stablecoins details
        holdings_text += "\nSTABLECOINS:\n"
        for symbol, data in stablecoins.items():
            allocation_pct = (data['value_brl'] / total_value) * 100
            holdings_text += f"- {symbol}:\n"
            holdings_text += f"  * Quantidade: {data['amount']:.8f}\n"
            holdings_text += f"  * Valor: R$ {data['value_brl']:.2f}\n"
            holdings_text += f"  * Alocação: {allocation_pct:.1f}%\n\n"
        
        # Add rebalancing analysis
        holdings_text += f"\nANÁLISE DE BALANCEAMENTO (Estratégia 70-30):\n"
        crypto_allocation = (current_crypto_value/total_value)*100
        stable_allocation = (current_stable_value/total_value)*100
        
        holdings_text += f"- Valor Total do Portfólio: R$ {total_value:.2f}\n"
        holdings_text += f"- Alocação Atual em Crypto: R$ {current_crypto_value:.2f} ({crypto_allocation:.1f}%)\n"
        holdings_text += f"- Alocação Atual em Stablecoins: R$ {current_stable_value:.2f} ({stable_allocation:.1f}%)\n\n"
        
        # Format the analysis request
        user_prompt = user_prompt_template.format(
            timestamp=current_time,
            portfolio_data=holdings_text
        )

        # Create chat completion
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

        return {
            "analysis": response.choices[0].message.content,
            "timestamp": current_time
        }
    except Exception as e:
        error_msg = f"Error getting AI analysis: {e}\n{traceback.format_exc()}"
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
        return jsonify({'error': 'Portfolio not found'}), 404
    
    prices = get_crypto_prices(list(portfolio.keys()))
    
    if not prices:
        return jsonify({'error': 'Unable to fetch current prices'}), 500
    
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
    
    return jsonify(portfolio_data)

@app.route('/api/portfolio/update', methods=['POST'])
def update_portfolio():
    """Update portfolio asset quantities"""
    try:
        data = request.get_json()
        if not data or 'assets' not in data:
            return jsonify({'error': 'Invalid request data'}), 400

        # Load current portfolio
        current_portfolio = load_portfolio()
        if not current_portfolio:
            return jsonify({'error': 'Failed to load current portfolio'}), 500

        # Update quantities
        for symbol, amount in data['assets'].items():
            try:
                current_portfolio[symbol] = float(amount)
            except (ValueError, TypeError) as e:
                return jsonify({'error': f'Invalid amount for {symbol}: {str(e)}'}), 400

        # Save updated portfolio
        if save_portfolio(current_portfolio):
            return jsonify({'message': 'Portfolio updated successfully', 'portfolio': current_portfolio})
        else:
            return jsonify({'error': 'Failed to save portfolio'}), 500

    except Exception as e:
        error_msg = f"Error updating portfolio: {str(e)}"
        print(error_msg)
        return jsonify({'error': error_msg}), 500

@app.route('/api/portfolio/analysis', methods=['GET'])
def get_portfolio_analysis():
    """Get portfolio with AI analysis"""
    try:
        portfolio = load_portfolio()
        if not portfolio:
            print("No portfolio data found")
            return jsonify({'error': 'Portfolio not found'}), 404
        
        print(f"Portfolio loaded: {portfolio}")
        
        prices = get_crypto_prices(list(portfolio.keys()))
        if not prices:
            print("Failed to fetch crypto prices")
            return jsonify({'error': 'Unable to fetch current prices'}), 500
        
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
            return jsonify({'error': analysis_result['error']}), 500
        
        print("Analysis completed successfully")
        
        return jsonify({
            'portfolio': portfolio_data,
            'analysis': analysis_result['analysis'],
            'timestamp': analysis_result['timestamp']
        })
        
    except Exception as e:
        error_msg = f"Error in portfolio analysis: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
