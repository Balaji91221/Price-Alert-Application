# Price Alert Application

A web application that allows users to set price alerts for cryptocurrencies. When the price of a cryptocurrency reaches the target set by the user, an email notification is sent.

## Features

- User registration and authentication using JWT.
- Set and manage price alerts for cryptocurrencies.
- Real-time price updates using Binance WebSocket.
- Email notifications using SMTP.
- PostgreSQL for database management.
- Docker Compose setup for easy deployment.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Backend Setup](#backend-setup)
3. [Frontend Setup](#frontend-setup)
4. [Database Setup](#database-setup)
5. [Running the Project](#running-the-project)
6. [Endpoints Documentation](#endpoints-documentation)
7. [Troubleshooting](#troubleshooting)

## Project Structure

price-alert-app/
│                               
├── backend/     
│ ├── app.py    
│ ├── models.py  
│ ├── requirements.txt    
│ ├── Dockerfile        
│ └── docker-compose.yml    
│            
├── frontend/       
│ ├── src/    
│ ├── public/    
│ ├── package.json    
│ ├── Dockerfile    
│   
│
└── README.md


## Backend Setup

### Prerequisites

- Python 3.8 or higher
- PostgreSQL
- Docker (optional, for Docker Compose)

### Installation

1. **Clone the repository:**

    ```bash
    git clone 
    cd price-alert-app/backend
    ```

2. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Configure your database:**

    Update `DATABASE_URL` in `app.py` with your PostgreSQL connection string.

4. **Run the backend server:**

    ```bash
    uvicorn app:app --reload
    ```

   The backend server will run at `http://127.0.0.1:8000`.

### Docker Setup

1. **Create a `Dockerfile` in the `backend` directory:**

    ```dockerfile
    # Dockerfile
    FROM python:3.8

    WORKDIR /app

    COPY requirements.txt requirements.txt
    RUN pip install -r requirements.txt

    COPY . .

    CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
    ```

2. **Create a `docker-compose.yml` file in the `backend` directory:**

    ```yaml
    # docker-compose.yml
    version: '3'

    services:
      db:
        image: postgres:13
        environment:
          POSTGRES_USER: example_owner
          POSTGRES_PASSWORD: yourpassword
          POSTGRES_DB: example
        ports:
          - "5432:5432"

      backend:
        build: .
        ports:
          - "8000:8000"
        depends_on:
          - db
    ```

3. **Build and run the Docker container:**

    ```bash
    docker-compose up --build
    ```

## Frontend Setup

### Prerequisites

- Node.js (v14 or later)
- Docker (optional, for Docker Compose)

### Installation

1. **Navigate to the frontend directory:**

    ```bash
    cd price-alert-app/frontend
    ```

2. **Install dependencies:**

    ```bash
    npm install
    ```

3. **Run the frontend server:**

    ```bash
    npm start
    ```

   The frontend server will run at `http://localhost:3000`.

### Docker Setup

1. **Create a `Dockerfile` in the `frontend` directory:**

    ```dockerfile
    # Dockerfile
    FROM node:14

    WORKDIR /app

    COPY package.json package-lock.json ./
    RUN npm install

    COPY . .

    CMD ["npm", "start"]
    ```

2. **Create a `docker-compose.yml` file in the `frontend` directory:**

    ```yaml
    # docker-compose.yml
    version: '3'

    services:
      frontend:
        build: .
        ports:
          - "3000:3000"
    ```

3. **Build and run the Docker container:**

    ```bash
    docker-compose up --build
    ```

## Database Setup

### PostgreSQL Configuration

- Use Neon Tech PostgreSQL for managed database hosting.
- Configure the `DATABASE_URL` in the `backend/app.py` file with the connection string provided by Neon Tech.

## Running the Project

1. **Start the backend and database:**

    ```bash
    cd price-alert-app/backend
    docker-compose up
    ```

2. **Start the frontend:**

    ```bash
    cd price-alert-app/frontend
    npm start
    ```

3. **Access the application:**

   - Frontend: `http://localhost:3000`
   - Backend API: `http://127.0.0.1:8000`

## Endpoints Documentation

### Authentication

- **POST** `/register` - Register a new user.
  - Request Body: 
    ```json
    {
      "username": "string",
      "password": "string",
      "email": "string"
    }
    ```
  - Response: 
    ```json
    {
      "username": "string"
    }
    ```

- **POST** `/token` - Log in and get a JWT token.
  - Request Body: 
    ```json
    {
      "username": "string",
      "password": "string"
    }
    ```
  - Response: 
    ```json
    {
      "access_token": "string",
      "token_type": "bearer"
    }
    ```

### Alerts

- **POST** `/alerts/create/` - Create a new price alert.
  - Request Body: 
    ```json
    {
      "coin_id": "string",
      "target_price": "number"
    }
    ```
  - Response: 
    ```json
    {
      "id": "integer",
      "coin_id": "string",
      "target_price": "number",
      "status": "string",
      "created_at": "datetime"
    }
    ```

- **DELETE** `/alerts/delete/{alert_id}` - Delete an existing price alert.
  - Response: 
    ```json
    {
      "detail": "Alert deleted"
    }
    ```

- **GET** `/alerts/` - Fetch all alerts for the authenticated user.
  - Query Params: `status`, `skip`, `limit`
  - Response: 
    ```json
    [
      {
        "id": "integer",
        "coin_id": "string",
        "target_price": "number",
        "status": "string",
        "created_at": "datetime"
      },
      ...
    ]
    ```

## Troubleshooting

- **CORS Issues:** Ensure that CORS settings in `app.py` allow requests from `http://localhost:3000`.
- **Database Connection:** Verify that the `DATABASE_URL` is correctly configured.
- **Backend Not Starting:** Check for any error messages in the logs and ensure that all dependencies are installed.



