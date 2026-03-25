"""
PlugForge API - Centralized backend for all PlugForge plugins
"""
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Security: Limit request size to 16KB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024  # 16KB

# Register blueprints
from src.calsync import calsync_bp, limiter, rate_limit_handler
app.register_blueprint(calsync_bp, url_prefix='/calsync')

# Initialize rate limiter with app
limiter.init_app(app)

# Register rate limit error handler
app.errorhandler(429)(rate_limit_handler)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "service": "plugforge-api"
    })

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        "status": "ok",
        "service": "plugforge-api",
        "version": "1.0.0",
        "plugins": ["calsync"]
    })

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle request too large errors"""
    return jsonify({"error": "Request too large"}), 413

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
