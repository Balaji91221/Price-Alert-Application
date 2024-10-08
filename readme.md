# tanX-Backend-price-alert

This application allows users to set price alerts for cryptocurrencies. When the target price is achieved, the user receives an email notification. The application is built using Flask, SQLAlchemy, and WebSocket for real-time price updates.


##### Assignmnet Submitted By: Kelavath Balaji Naik(21BCE9738 ), VIT-AP,  Amaravati
## Getting Started

### Prerequisites
- Docker 

### Steps to Run

1. Ensure Docker is installed on your system. If not, download and install it from [Docker](https://www.docker.com/products/docker-desktop).

2. Open a terminal and run the following command to build and start the application:
   ```bash
   docker-compose up -d --build
   ```
3.Access the endpoint at:
```http://localhost:5000```

### Endpoints
Once a user signs up or logs into the system, the following functionalities are implemented:
#### There are following things implemented using JWT token. 
1. REST API endpoint for the user’s to create an alert `alerts/create/`
2. REST API endpoint for the user’s to delete an alert `alerts/delete/`
3. REST API endpoint to fetch all the alerts that the user has created along with the included filter options based on the status of the alerts, paginated the response and status of the alerts as (created/deleted/triggered).

### 1. User Signup
- **Endpoint:** `/signup`
- **Method:** `POST`
- **Description:** Allows a user to sign up by providing a username, password, and email in the request body.

### 2. User Login
- **Endpoint:** `/login`
- **Method:** `POST`
- **Description:** Allows a user to log in by providing a username and password in the request body. Returns an access token for authenticated requests.

### 3. Create/Update Alert
- **Endpoint:** `/alerts/create`
- **Method:** `POST`
- **Authorization:** Bearer Token (JWT)
- **Description:** Creates or updates an alert for a user. Requires a valid JWT token. The request body should contain information about the coin and target price.

### 4. Delete Alert (Mark as Deleted)
- **Endpoint:** `/alerts/delete/<int:alert_id>`
- **Method:** `DELETE`
- **Authorization:** Bearer Token (JWT)
- **Description:** Marks an alert as deleted. Requires a valid JWT token and the ID of the alert to be deleted.

### 5. Delete Alert (Delete Row)
- **Endpoint:** `/alerts/delete/real/<int:alert_id>`
- **Method:** `DELETE`
- **Authorization:** Bearer Token (JWT)
- **Description:** Deletes an alert row from the database. Requires a valid JWT token and the ID of the alert to be deleted.

### 6. Get User Alerts
- **Endpoint:** `/alerts`
- **Method:** `GET`
- **Authorization:** Bearer Token (JWT)
- **Description:** Fetches alerts for the authenticated user. Supports pagination and optional status filtering.

### 7. Get User Alerts by Status
- **Endpoint:** `/alerts/<status>`
- **Method:** `GET`
- **Authorization:** Bearer Token (JWT)
- **Description:** Fetches alerts for the authenticated user based on the specified status (e.g., created, deleted, triggered).

# API Documentation
These apis were successfully tested using postman during development process. The database model dump file is uploaded for successfull composing of docker inorder to run this project.
## Endpoints

### 1. User Signup

- **Endpoint:** `/signup`
- **Method:** `POST`
- **Description:** Creates a new user account.
- **Request Body:**
  ```json
  {
    "username": "example_user",
    "password": "secure_password",
    "email": "user@example.com"
  }

  ### Response:
  {
    "message": "User signed up successfully"
  }


### 2. User Login

- **Endpoint:** `/login`
- **Method:** `POST`
- **Description:** Authenticates and logs in a user.
- **Request Body:**
  ```json
  {
    "username": "example_user",
    "password": "secure_password"
  }
  ### Response
  {
    "message": "Login successful",
    "access_token": "<access_token>"
  }


### 3. Create/Update Alert

- **Endpoint:** `/alerts/create`
- **Method:** `POST`
- **Authorization:** Bearer Token (JWT)
- **Description:** Creates or updates an alert for a specific cryptocurrency.
- **Request Body:**
  ```json
  {
    "coin": "BTC",
    "target_price": 50000.0
  }
  Response:
  {
    "message": "Alert created successfully"
  }



### 4. Mark Alert as Deleted

- **Endpoint:** `/alerts/delete/<int:alert_id>`
- **Method:** `DELETE`
- **Authorization:** Bearer Token (JWT)
- **Description:** Marks an alert as deleted.
- **Response:**
  ```json
  {
    "message": "Alert marked as deleted"
  }


### 5. Delete Alert

- **Endpoint:** `/alerts/delete/real/<int:alert_id>`
- **Method:** `DELETE`
- **Authorization:** Bearer Token (JWT)
- **Description:** Deletes an alert from the database.
- **Response:**
  ```json
  {
    "message": "Alert deleted successfully"
  }


### 6. Get User Alerts

- **Endpoint:** `/alerts`
- **Method:** `GET`
- **Authorization:** Bearer Token (JWT)
- **Description:** Fetches user alerts with optional filtering and pagination.
- **Query Parameters:**
  - `page`: Current page number (default: 1)
  - `per_page`: Alerts per page (default: 10)
  - `status`: Filter alerts by status (optional)
- **Response:**
  ```json
  {
    "alerts": [
      {
        "id": 1,
        "coin": "BTC",
        "target_price": 50000.0,
        "status": "created"
      },
      // ... (other alerts)
    ]
  }


### 7. Get User Alerts by Status

- **Endpoint:** `/alerts/<status>`
- **Method:** `GET`
- **Authorization:** Bearer Token (JWT)
- **Description:** Fetches user alerts based on status.
- **Path Parameter:**
  - `status`: Alert status (e.g., created, deleted, triggered)
- **Response:**
  ```json
  {
    "alerts": [
      {
        "id": 1,
        "coin": "BTC",
        "target_price": 50000.0,
        "status": "created"
      },
      // ... (other alerts)
    ]
  }





## Web Socket

### 1. Coin Price WebSocket
- **URL:** `wss://stream.binance.com/ws`
- **Description:** WebSocket connection for real-time updates on cryptocurrency prices. Used internally for triggering alerts when the target price is reached.

## Sending Alerts

When the WebSocket receives real-time price updates for cryptocurrencies, it checks if the current price satisfies the target conditions set by users in their alerts. If a match is found, the alert is triggered, and the notification system is initiated.
## Solution for getting price alerts
1. We use the WebSocket Client library to connect to binance web socket  
2. Use of subscription to subscribe to kline streams such as `btcusdt@kline_1m` or `ethusdt@kline_1m`
3. Each message received from the stream is processed by `on_message` function which also checks for alert
    by querying the alerts table. On fulfillment of alert, we update the database and for any changes on the
    subscription list (mainted as a dictionary) we unsubscribe and resubscribe to a new list of subscription.

### Solution Explained as Pub-Sub:
The described solution exhibits characteristics of a publish-subscribe (pub-sub) pattern. In a traditional pub-sub architecture:

1. Publisher: Binance WebSocket acts as a publisher, continuously streaming real-time price updates for various cryptocurrencies.

2. Subscribers: The application, specifically the on_message function, acts as a subscriber, subscribing to specific kline streams (channels) of interest.

When an alert condition is met, the alert system in the application acts as a mechanism to "publish" this information to the users who have set up alerts. The users, in this context, are the "subscribers" who are interested in specific cryptocurrency price updates.

The WebSocket communication, where the server (Binance WebSocket) sends messages to multiple clients (your application), aligns with the basic concept of pub-sub.

### Notification Workflow

1. **WebSocket Handling:**
   - The WebSocket continuously receives real-time price updates from the Binance WebSocket (`wss://stream.binance.com/ws`).
   - Upon receiving an update, it extracts relevant information such as the coin symbol and current price.
   - WebSocket setup in on_open function:
     ```python
     SOCK_URL = f"wss://stream.binance.com/ws"

      WEB_SOCKET = websocket.WebSocketApp(SOCK_URL, on_open=on_open, on_close=on_close, on_message=on_message, on_error=on_error)
      
      wsThread = threading.Thread(target=WEB_SOCKET.run_forever)
      wsThread.daemon = True
      wsThread.start()
      ```
   - Handling WebSocket messages in on_message function:
     ```python
         def on_message(ws, message):
          data = json.loads(message)
          reqMsg = {"coin": data["s"][:-4].upper(), "price": float(data["k"]["c"])}
      
          # Additional code for handling alerts and user emails (see step 2 and 3)
     ```
2. **Alert Matching:**
   - The extracted information is then compared with the active alerts stored in the database.
   - For each active alert that matches the conditions (coin symbol and target price), the alert is marked as triggered, and the user is identified.
   - Querying for satisfying alerts in on_message function:
      ```python
         satisfyingAlerts = Alert.query.filter(Alert.status == 'created', Alert.coin == reqMsg["coin"], Alert.target_price <= reqMsg["price"]).all()
     ```
   - Updating alert status to 'triggered' in on_message function:
   ```python
      for alert in satisfyingAlerts:
          alert.status = 'triggered'
   ```

4. **User Identification:**
   - The system retrieves the user details associated with the triggered alert, including their email address.
   - Retrieving user details associated with the triggered alert in on_message function:
     ```python
        userDetails = []

      for alert in satisfyingAlerts:
          userDetails.append({'email': User.query.filter(User.id == alert.user_id).first().email,'coin': reqMsg["coin"], 'price': reqMsg["coin"]})
     ```

5. **Email Notification:**
   - The system sends an email notification to the identified user, informing them that their specified coin has reached the target price.
   - The email contains a message thanking the user and providing details about the triggered alert.
   -Sending email notifications in on_message function:
   ```python
      for user_detail in userDetails:
          email_value = user_detail['email']
          coin_name = user_detail['coin']
          send_email(email_value, coin_name, s)
   ```

### Email Configuration

Email notifications are sent using the SMTP (Simple Mail Transfer Protocol) with the following configuration:

- **SMTP Server:** `smtp.office365.com`
- **Port:** `587`
- **Security:** `STARTTLS`
- **Authentication:** The system logs in to the SMTP server using the credentials (`cointargetalert@outlook.com`, `******`).

### Example Email Content

The email sent to users when their alert is triggered has the following structure:

- **Subject:** Target Alert
- **Body:** ```TEXT = f'Dear User, \n The coin {coin_name} that you set for alert has reached its target.\n Thank you.'```


## Additional Notes

- The WebSocket runs in a separate thread (`wsThread`) and establishes a connection to the Binance WebSocket for real-time price updates.
- The Flask application manages user alerts and WebSocket subscriptions, ensuring that users receive notifications only for the specified coins.
- The solution includes error handling for SMTP connection/authentication errors and WebSocket connection timeouts.

## Coin Alert System - Database Model

## User Table

The `User` table is responsible for storing user information.

### User Attributes

- `id`: Integer, Primary Key
- `username`: String (50 characters), Unique, Not Null
- `password`: String (50 characters), Not Null
- `email`: String (100 characters), Not Null

## Alert Table

The `Alert` table manages cryptocurrency alerts set by users.

### Alert Attributes

- `id`: Integer, Primary Key
- `user_id`: Integer, Foreign Key (references User.id), Not Null
- `coin`: String (10 characters), Not Null
- `target_price`: Float, Not Null
- `status`: String (20 characters), Default: 'created'

The `status` field denotes the current state of the alert, with potential values including 'created,' 'deleted,' or 'triggered.'

The `user_id` field establishes a foreign key relationship with the `id` field in the `User` table, connecting each alert to a specific user.


