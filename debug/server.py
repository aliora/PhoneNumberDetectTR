"""
Debug Web Server - Flask

Test amaçlı web arayüzü ve webhook endpoint'i sağlar.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
import requests
from config.settings import settings

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/debug_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('debug_server')

app = Flask(__name__, 
            template_folder='.',
            static_folder='static')

# Sonuçları bellekte tut (test için)
results_store = {}


@app.route('/')
def index():
    """Ana sayfa"""
    return send_from_directory('.', 'index.html')


@app.route('/api/submit', methods=['POST'])
def submit_job():
    """
    OCR işi gönder (receiver servisine proxy)
    """
    try:
        data = request.get_json()
        
        # Receiver servisine istek gönder
        receiver_url = f"http://localhost:{settings.api.receiver_port}/process"
        
        # Callback URL'i bu sunucuya ayarla
        callback_url = f"http://localhost:{settings.api.debug_port}/api/webhook"
        
        payload = {
            'image_url': data['image_url'],
            'user_id': data['user_id'],
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'callback_url': callback_url
        }
        
        response = requests.post(receiver_url, json=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        task_id = result['task_id']
        
        # Task'ı pending olarak kaydet
        results_store[task_id] = {
            'status': 'pending',
            'submitted_at': datetime.now().isoformat()
        }
        
        logger.info(f"Job submitted - task_id: {task_id}")
        
        return jsonify(result), response.status_code
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to submit job: {str(e)}")
        return jsonify({
            'error': 'Failed to submit job',
            'details': str(e)
        }), 503
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            'error': 'Internal error',
            'details': str(e)
        }), 500


@app.route('/api/webhook', methods=['POST'])
def webhook():
    """
    Sender servisinden gelen webhook callback'i al
    """
    try:
        result = request.get_json()
        task_id = result.get('task_id')
        
        if task_id:
            results_store[task_id] = result
            logger.info(f"Webhook received - task_id: {task_id}, status: {result.get('status')}")
            
            return jsonify({'status': 'received'}), 200
        else:
            return jsonify({'error': 'task_id missing'}), 400
            
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/result/<task_id>', methods=['GET'])
def get_result(task_id):
    """
    Task ID ile sonuç sorgula
    """
    try:
        # Önce local store'a bak
        if task_id in results_store:
            logger.info(f"Result from local store - task_id: {task_id}")
            return jsonify(results_store[task_id]), 200
        
        # Local'de yoksa receiver'dan sorgula
        receiver_url = f"http://localhost:{settings.api.receiver_port}/result/{task_id}"
        response = requests.get(receiver_url, timeout=5)
        response.raise_for_status()
        
        result = response.json()
        
        # Cache'e al
        if result.get('status') != 'processing':
            results_store[task_id] = result
        
        logger.info(f"Result from receiver - task_id: {task_id}, status: {result.get('status')}")
        
        return jsonify(result), 200
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get result: {str(e)}")
        return jsonify({
            'error': 'Failed to get result',
            'details': str(e)
        }), 503
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            'error': 'Internal error',
            'details': str(e)
        }), 500


@app.route('/api/results', methods=['GET'])
def get_all_results():
    """
    Tüm sonuçları listele (debug için)
    """
    return jsonify(results_store), 200


@app.route('/api/status', methods=['GET'])
def status():
    """
    Servis durumu
    """
    try:
        # Receiver durumunu kontrol et
        receiver_url = f"http://localhost:{settings.api.receiver_port}/status"
        response = requests.get(receiver_url, timeout=5)
        receiver_status = response.json() if response.ok else None
        
        return jsonify({
            'debug_server': 'healthy',
            'receiver_service': receiver_status,
            'cached_results': len(results_store),
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'debug_server': 'healthy',
            'receiver_service': 'unavailable',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 200


if __name__ == '__main__':
    logger.info(f"Starting Debug Server on {settings.api.debug_host}:{settings.api.debug_port}")
    
    app.run(
        host=settings.api.debug_host,
        port=settings.api.debug_port,
        debug=True
    )
