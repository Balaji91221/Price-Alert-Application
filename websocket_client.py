# app.py
import os
import json
import time
import logging
import threading
import smtplib
from datetime import timedelta
from collections import defaultdict

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
import websocket

# Configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SECRET_KEY'] = 'your_jwt_secret_key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

jwt = JWTManager(app)
db = SQLAlchemy(app)

# WebSocket and Subscription Management
BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"
subscriptions = defaultdict(int)
WEB_SOCKET = None

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    coin = db.Column(db.String(10), nullable=False)
    target_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='created')

# Helper Functions
def connect_to_smtp_server():
    try:
        s = smtplib.SMTP('smtp.office365.com', 587)
        s.starttls()
        s.login("cointargetalert@outlook.com", "Outlook99")
        return s
    except smtplib.SMTPException as e:
        logger.error("SMTP Connection Error: %s", str(e))
        return None

def send_email(user_email, coin_name, smtp_email_obj):
    SUBJECT = 'Target Alert'
    TEXT = f'Dear User, \n The coin {coin_name} that you set for alert has reached its target.\n Thank you.'
    message = f'Subject: {SUBJECT}\n\n{TEXT}'
    smtp_email_obj.sendmail("cointargetalert@outlook.com", user_email, message)
    smtp_email_obj.quit()

def unsubscribe_from_socket(lst):
    if WEB_SOCKET:
        WEB_SOCKET.send(json.dumps({"method": "UNSUBSCRIBE", "params": lst, "id": 312}))

def send_to_socket(lst):
    if WEB_SOCKET:
        WEB_SOCKET.send(json.dumps({"method": "SUBSCRIBE", "params": lst, "id": 1}))

# WebSocket Handlers
def on_message(ws, message):
    try:
        data = json.loads(message)
        req_msg = {"coin": data["s"][:-4].upper(), "price": float(data["k"]["c"])}
        logger.info("Received message: %s", req_msg)

        with app.app_context():
            satisfying_alerts = Alert.query.filter(Alert.status == 'created', Alert.coin == req_msg["coin"],
                                                   Alert.target_price <= req_msg["price"]).all()
            
            user_details = []
            old_subscriptions = subscriptions.copy()

            for alert in satisfying_alerts:
                user = User.query.filter_by(id=alert.user_id).first()
                if user:
                    user_details.append({'email': user.email, 'coin': req_msg["coin"]})

                key = req_msg["coin"].lower() + "usdt@kline_1m"
                if subscriptions[key] == 1:
                    del subscriptions[key]
                else:
                    subscriptions[key] -= 1

                alert.status = 'triggered'

            if user_details:
                db.session.commit()
                smtp_server = connect_to_smtp_server()
                for detail in user_details:
                    send_email(detail['email'], req_msg["coin"], smtp_server)
                logger.info("Triggered alerts for: %s", user_details)

            if old_subscriptions.keys() != subscriptions.keys():
                unsubscribe_from_socket(list(old_subscriptions.keys()))
                send_to_socket(list(subscriptions.keys()))

    except (json.JSONDecodeError, KeyError) as e:
        logger.error("Error processing message: %s", e)

def on_close(ws, close_status_code, close_msg):
    logger.info("WebSocket closed. Code: %d, Message: %s", close_status_code, close_msg)
    time.sleep(5)
    create_socket()

def on_open(ws):
    logger.info("WebSocket connection opened")
    send_to_socket(list(subscriptions.keys()))

def on_error(ws, error):
    logger.error("WebSocket error: %s", error)

def create_socket():
    ws = websocket.WebSocketApp(BINANCE_WS_URL, on_open=on_open, on_close=on_close, on_message=on_message, on_error=on_error)

    def run_sock():
        while True:
            try:
                ws.run_forever()
            except Exception as e:
                logger.error("WebSocket run_forever error: %s", e)
                time.sleep(5)

    ws_thread = threading.Thread(target=run_sock)
    ws_thread.daemon = True
    ws_thread.start()

    return ws

# Routes
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    if not all(key in data for key in ('username', 'password', 'email')):
        return jsonify({'message': 'Missing required fields'}), 400

    new_user = User(username=data['username'], password=data['password'], email=data['email'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User signed up successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and user.password == data['password']:
        access_token = create_access_token(identity=user.id)
        return jsonify({'message': 'Login successful', 'access_token': access_token}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/alerts/create', methods=['POST'])
@jwt_required()
def create_alert():
    data = request.get_json()
    if 'coin' not in data or 'target_price' not in data:
        return jsonify({'message': 'Missing required fields (coin and target_price)'}), 400

    current_user_id = get_jwt_identity()
    existing_alert = Alert.query.filter_by(user_id=current_user_id, coin=data['coin']).first()

    if existing_alert:
        if existing_alert.status == 'deleted':
            existing_alert.status = 'created'
            db.session.commit()
            return jsonify({'message': 'Alert updated successfully'}), 200
        return jsonify({'message': 'You already have an alert for this coin'}), 400

    new_alert = Alert(user_id=current_user_id, coin=data['coin'], target_price=data['target_price'])
    db.session.add(new_alert)
    db.session.commit()

    unsubscribe_from_socket(list(subscriptions.keys()))
    subscriptions[data["coin"].lower() + "usdt@kline_1m"] += 1
    send_to_socket(list(subscriptions.keys()))

    return jsonify({'message': 'Alert created successfully'}), 201

@app.route('/alerts/delete/<int:alert_id>', methods=['DELETE'])
@jwt_required()
def delete_alert(alert_id):
    current_user_id = get_jwt_identity()
    alert = Alert.query.filter_by(id=alert_id, user_id=current_user_id).first()

    if alert:
        alert.status = 'deleted'
        db.session.commit()
        return jsonify({'message': 'Alert marked as deleted'}), 200
    return jsonify({'message': 'Alert not found or unauthorized'}), 404

@app.route('/alerts/delete/real/<int:alert_id>', methods=['DELETE'])
@jwt_required()
def delete_alert_delete_row(alert_id):
    current_user_id = get_jwt_identity()
    alert = Alert.query.filter_by(id=alert_id, user_id=current_user_id).first()

    if alert:
        db.session.delete(alert)
        db.session.commit()
        return jsonify({'message': 'Alert deleted successfully'})
    return jsonify({'message': 'Alert not found or unauthorized'}), 404

@app.route('/alerts', methods=['GET'])
@jwt_required()
def get_user_alerts():
    current_user_id = get_jwt_identity()
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=10, type=int)
    status_filter = request.args.get('status', type=str)

    alerts_query = Alert.query.filter_by(user_id=current_user_id, status=status_filter or 'created')
    alerts = alerts_query.paginate(page=page, per_page=per_page, error_out=False)

    if not alerts.items:
        return jsonify({'message': 'No alerts found for the current user'}), 404

    alert_list = [{
        'id': alert.id,
        'coin': alert.coin,
                'target_price': alert.target_price,
        'status': alert.status
    } for alert in alerts.items]

    response_headers = {
        'X-Total-Count': alerts.total,
        'X-Total-Pages': alerts.pages,
        'X-Current-Page': alerts.page,
        'X-Per-Page': per_page
    }

    return jsonify({'alerts': alert_list}), 200, response_headers

@app.route('/alerts/<status>', methods=['GET'])
@jwt_required()
def get_user_alerts_by_status(status):
    current_user_id = get_jwt_identity()
    valid_statuses = ['created', 'deleted', 'triggered']
    if status not in valid_statuses:
        return jsonify({'message': 'Invalid status provided'}), 400

    alerts = Alert.query.filter_by(user_id=current_user_id, status=status).all()

    if not alerts:
        return jsonify({'message': f'No {status} alerts found for the current user'}), 404

    alert_list = [{
        'id': alert.id,
        'coin': alert.coin,
        'target_price': alert.target_price,
        'status': alert.status
    } for alert in alerts]

    return jsonify({'alerts': alert_list})

# WebSocket Initialization
def init_websocket():
    global WEB_SOCKET
    WEB_SOCKET = create_socket()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        alerts = Alert.query.filter(Alert.status == 'created').all()
        for alert in alerts:
            subscriptions[alert.coin.lower() + "usdt@kline_1m"] += 1
        
        send_to_socket(list(subscriptions.keys()))

    init_websocket()
    
    try:
        app.run(debug=True, host='0.0.0.0')
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    finally:
        if WEB_SOCKET:
            WEB_SOCKET.close()
            logger.info("WebSocket closed")

