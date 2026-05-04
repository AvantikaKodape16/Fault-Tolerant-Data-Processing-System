from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import os
import json

app = Flask(__name__)
CORS(app)

# Load schema configuration
try:
    with open('schema_config.json', 'r') as f:
        SCHEMA_CONFIG = json.load(f)
except Exception as e:
    print(f"Warning: Could not load schema config: {e}")
    SCHEMA_CONFIG = {'clients': {'default': {}}}

# Make schema config available globally
app.config['SCHEMA_CONFIG'] = SCHEMA_CONFIG

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data_processing.db')
engine = create_engine(DATABASE_URL, echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Middleware to inject session
@app.before_request
def get_db():
    from flask import g
    g.db = Session()

@app.teardown_appcontext
def shutdown_session(exception=None):
    from flask import g
    if hasattr(g, 'db'):
        g.db.close()

# Routes
@app.route('/api/events', methods=['POST'])
def ingest_event():
    from flask import g
    from routes import ingest_event as route_ingest
    return route_ingest(g.db, app.config['SCHEMA_CONFIG'])

@app.route('/api/aggregates', methods=['GET'])
def get_aggregates_route():
    from flask import g
    from routes import get_aggregates as route_aggregates
    return route_aggregates(g.db)

@app.route('/api/events/status', methods=['GET'])
def get_events_status_route():
    from flask import g
    from routes import get_events_status as route_status
    return route_status(g.db)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'version': '1.0.0'}), 200

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)