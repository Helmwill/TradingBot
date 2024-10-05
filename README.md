# Crypto Trading Bot

This project is a cryptocurrency trading bot designed to perform both manual and automatic trades using the Coinbase API. It features an integrated trading strategy that allows it to make buying and selling decisions based on market data. The bot leverages an AWS RDS instance for its database, and the deployment process is being containerized using Docker to run on AWS ECS and EC2 instances.

## Features
- **Manual Trading**: Users can manually execute buy and sell trades for supported cryptocurrencies.
- **Automated Trading**: The bot uses a trading strategy to make automated trading decisions.
- **Historical Data Retrieval**: Fetch historical price data from Coinbase to make informed trading decisions.
- **Current Price Retrieval**: Get real-time price data for selected cryptocurrencies.

## Technologies Used
- **Backend**: Django & Django REST Framework (DRF)
- **Database**: AWS RDS (MySQL)
- **Authentication**: JWT-based authentication using `rest_framework_simplejwt`
- **External API**: Coinbase API for price data and trade execution
- **Containerization**: Docker (in progress)
- **Cloud Services**: AWS ECS and EC2 (in progress)

## Setup Instructions

### Prerequisites
- Python 3.8+
- Docker (for containerization)
- AWS account with RDS, ECS, and EC2 access
- A Coinbase Pro account with API keys for sandbox and production environments
- `secure_keys.env` file with the following environment variables:
  - `DJANGO_SECRET_KEY`
  - `API_KEY_SANDBOX`
  - `API_SECRET_SANDBOX`
  - `API_PASSPHRASE_SANDBOX`
  - `AWS_DB_NAME`, `AWS_DB_USER`, `AWS_DB_PASSWORD`, `AWS_DB_HOST`, `AWS_DB_PORT`

### Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/crypto-trading-bot.git
   cd crypto-trading-bot
   ```

2. Set up a virtual environment and install dependencies:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. Set up environment variables by creating a `secure_keys.env` file in the root directory or use environment variables for CI/CD.

4. Apply database migrations:
   ```sh
   python manage.py migrate
   ```

5. Create a superuser to access the Django admin:
   ```sh
   python manage.py createsuperuser
   ```

6. Start the development server:
   ```sh
   python manage.py runserver
   ```

### Running Tests
To run tests, use the following command:
```sh
python manage.py test
```
Tests include unit tests for views, models, and trading strategies. Mocks are used to simulate API responses from Coinbase.

### Docker Containerization (In Progress)
1. Build the Docker image:
   ```sh
   docker build -t crypto-trading-bot .
   ```

2. Run the container:
   ```sh
   docker run -p 8000:8000 crypto-trading-bot
   ```

### AWS Deployment (In Progress)
The project will be deployed using AWS ECS and EC2 instances to ensure scalability. The database is managed using AWS RDS. The project also includes a mock server endpoint for testing purposes (`/mock/`).

## Usage
- **Manual Trading**: Users can send POST requests to endpoints to execute buy/sell orders.
- **Automated Trading**: The bot uses an internal trading strategy (`RecursiveTradingStrategy`) to decide when to buy or sell.

## API Endpoints
- `GET /health/`: Check the health status of the application.
- `GET /coinbase/historical/`: Fetch historical price data for a given product ID.
- `GET /current_prices/`: Fetch the current price for a given product ID.
- `POST /buy/`: Execute a buy order for a specified product ID and amount.
- `POST /sell/`: Execute a sell order for a specified product ID and amount.

## Environment Configuration
The bot uses a `.env` file to manage sensitive keys. Depending on the environment (`development`, `test`, or `production`), different API URLs and credentials are used, including sandbox credentials for testing.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.

## Contact
For any questions or inquiries, please contact `youremail@example.com`.
