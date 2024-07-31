from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_bcrypt import Bcrypt
from datetime import timedelta
from collections import defaultdict
import os
import json
import websocket
import threading
import time
import smtplib
import logging

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://example_owner:bpXemxKVZ9h0@ep-shy-recipe-a5cpzfqv.us-east-2.aws.neon.tech/example?sslmode=require'
)
app.config['SECRET_KEY'] = 'balaji91221'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
subscriptions = defaultdict(int)
WEB_SOCKET = None

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)  # Increased length to accommodate hashed passwords
    email = db.Column(db.String(100), nullable=False)

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    coin = db.Column(db.String(10), nullable=False)
    target_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='created')

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET'])
def signup_page():
    return render_template('signup.html')
@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()

        # Validate incoming data
        if 'username' not in data or 'password' not in data or 'email' not in data:
            return jsonify({'message': 'Missing required fields (username, password, and email)'}), 400

        # Check if the user already exists
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user:
            return jsonify({'message': 'Username already exists'}), 400

        # Create a new user
        new_user = User(username=data['username'], password=data['password'], email=data['email'])
        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': 'User signed up successfully'}), 201

    except Exception as e:
        app.logger.error(f'Error during signup: {e}')
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        user = User.query.filter_by(username=data['username']).first()

        if user and user.password == data['password']:
            access_token = create_access_token(identity=user.id)
            return jsonify({'message': 'Login successful', 'access_token': access_token}), 200
        else:
            return jsonify({'message': 'Invalid credentials'}), 401
    except Exception as e:
        app.logger.error(f'Error during login: {e}')
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/alerts/create', methods=['POST'])
@jwt_required()
def create_alert():
    data = request.get_json()
    if 'coin' not in data or 'target_price' not in data:
        return jsonify({'message': 'Missing required fields (coin, target_price)'}), 400

    current_user_id = get_jwt_identity()
    existing_alert = Alert.query.filter_by(user_id=current_user_id, coin=data['coin']).first()
    if existing_alert:
        if existing_alert.status == 'deleted':
            existing_alert.status = 'created'
            db.session.commit()
            return jsonify({'message': 'Alert updated successfully'}), 200
        else:
            return jsonify({'message': 'You already have an alert for this coin'}), 400

    new_alert = Alert(user_id=current_user_id, coin=data['coin'], target_price=data['target_price'])
    db.session.add(new_alert)
    db.session.commit()

    update_subscriptions(data["coin"].lower() + "usdt@kline_1m")

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
    else:
        return jsonify({'message': 'Alert not found or unauthorized'}), 404

@app.route('/alerts/delete/real/<int:alert_id>', methods=['DELETE'])
@jwt_required()
def delete_alert_delete_row(alert_id):
    current_user_id = get_jwt_identity()
    alert = Alert.query.filter_by(id=alert_id, user_id=current_user_id).first()
    if alert:
        db.session.delete(alert)
        db.session.commit()
        return jsonify({'message': 'Alert deleted successfully'}), 200
    else:
        return jsonify({'message': 'Alert not found or unauthorized'}), 404

@app.route('/alerts', methods=['GET'])
@jwt_required()
def get_user_alerts():
    current_user_id = get_jwt_identity()
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=10, type=int)
    status_filter = request.args.get('status', type=str)
    
    status_filter = 'created' if not status_filter else status_filter
    alerts_query = Alert.query.filter_by(user_id=current_user_id, status=status_filter)
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

    return jsonify({'alerts': alert_list}), 200

# WebSocket Functions
def update_subscriptions(coin_sub):
    global WEB_SOCKET
    if WEB_SOCKET:
        if subscriptions[coin_sub] == 0:
            unsubscribe_from_socket(list(subscriptions.keys()))
        subscriptions[coin_sub] += 1
        send_to_socket(list(subscriptions.keys()))

def unsubscribe_from_socket(sub_list):
    if WEB_SOCKET:
        WEB_SOCKET.send(json.dumps({"method": "UNSUBSCRIBE", "params": sub_list, "id": 312}))

def send_to_socket(sub_list):
    if WEB_SOCKET:
        WEB_SOCKET.send(json.dumps({"method": "SUBSCRIBE", "params": sub_list, "id": 1}))

def connect_to_smtp_server():
    try:
        smtp_server = smtplib.SMTP('smtp.office365.com', 587)
        smtp_server.starttls()
        smtp_server.login("kelavathbalajinaik115@gmail.com", "Balaji15@")
        return smtp_server
    except smtplib.SMTPConnectError:
        logger.error("SMTP Connection Error: Unable to connect to the SMTP server.")
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP Authentication Error: Incorrect email or password.")
    except smtplib.SMTPRecipientsRefused:
        logger.error("SMTP Recipients Refused: The recipient email address is invalid.")
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Exception: {str(e)}")
    return None

def send_email(user_email, coin_name, smtp_email_obj):
    SUBJECT = 'Target Alert'
    TEXT = f'Dear User,\nThe coin {coin_name} that you set for alert has reached its target.\nThank you.'
    message = f'Subject: {SUBJECT}\n\n{TEXT}'
    try:
        smtp_email_obj.sendmail("kelavathbalajinaik115@gmail.com", user_email, message)
    except Exception as e:
        logger.error(f"Error sending email: {e}")
    finally:
        smtp_email_obj.quit()

def on_message(ws, message):
    data = json.loads(message)
    try:
        coin = data["s"][:-4].upper()
        price = float(data["k"]["c"])
        logger.info(f"Received message: {{'coin': {coin}, 'price': {price}}}")

        with app.app_context():
            satisfying_alerts = Alert.query.filter(
                Alert.status == 'created',
                Alert.coin == coin,
                Alert.target_price <= price
            ).all()

            user_details = []
            old_subscriptions = subscriptions.copy()

            for alert in satisfying_alerts:
                user = User.query.filter_by(id=alert.user_id).first()
                if user:
                    user_details.append({'email': user.email, 'coin': coin, 'price': price})

                key = coin.lower() + "usdt@kline_1m"
                if subscriptions[key] == 1:
                    del subscriptions[key]
                else:
                    subscriptions[key] -= 1

                alert.status = 'triggered'
                smtp_email_obj = connect_to_smtp_server()
                if smtp_email_obj:
                    for user in user_details:
                        send_email(user['email'], user['coin'], smtp_email_obj)
                db.session.commit()

            unsubscribe_from_socket(list(old_subscriptions.keys()))
            send_to_socket(list(subscriptions.keys()))

    except Exception as e:
        logger.error(f"Error processing message: {e}")

def on_error(ws, error):
    logger.error(f"WebSocket Error: {error}")

def on_close(ws):
    logger.info("WebSocket closed")

def on_open(ws):
    logger.info("WebSocket opened")

def run_websocket():
    global WEB_SOCKET
    ws_url = "wss://stream.binance.com:9443/ws"
    while True:
        try:
            ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close)
            ws.on_open = on_open
            ws.run_forever()
        except Exception as e:
            logger.error(f"WebSocket Exception: {e}")
            time.sleep(5)  # Retry after a short delay

if __name__ == '__main__':
    # Run WebSocket in a separate thread
    ws_thread = threading.Thread(target=run_websocket)
    ws_thread.daemon = True
    ws_thread.start()
    logger.info("Starting Flask server on http://127.0.0.1:5000")
    app.run(debug=True)
