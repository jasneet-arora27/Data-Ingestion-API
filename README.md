# Data Ingestion API System

This project implements a simple Data Ingestion API System using FastAPI. The system allows users to submit data ingestion requests and check their processing status. It simulates fetching data from an external API and processes requests asynchronously while respecting rate limits and prioritization.

## Project Structure

```
data_ingestion_api
├── app
│   ├── main.py          # Entry point of the application
│   ├── models.py        # Data models and schemas
│   ├── routes.py        # API route definitions
│   ├── services.py      # Business logic for processing requests
│   ├── utils.py         # Utility functions
│   └── tests
│       ├── test_ingestion_api.py  # Unit tests for ingestion API
│       └── test_status_api.py      # Unit tests for status API
├── requirements.txt     # Project dependencies
├── README.md            # Project documentation
├── .env                 # Environment variables
└── .gitignore           # Git ignore file
```

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd data_ingestion_api
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access the API:**
   The API will be available at `http://localhost:8000`. You can use tools like Postman or curl to interact with the endpoints.

## API Endpoints

### Ingestion API

- **Endpoint:** `POST /ingest`
- **Request Body:**
  ```json
  {
    "ids": [1, 2, 3, 4, 5],
    "priority": "HIGH"
  }
  ```
- **Response:**
  ```json
  {
    "ingestion_id": "abc123"
  }
  ```

### Status API

- **Endpoint:** `GET /status/<ingestion_id>`
- **Response:**
  ```json
  {
    "ingestion_id": "abc123",
    "status": "triggered",
    "batches": [
      {
        "batch_id": "uuid",
        "ids": [1, 2, 3],
        "status": "completed"
      }
    ]
  }
  ```

## Testing

To run the tests, ensure the virtual environment is activated and execute:

```bash
pytest app/tests
```

## Notes

- The application simulates external API calls and processes requests in batches while respecting rate limits.
- Ensure to handle any environment-specific configurations in the `.env` file.

## License

This project is licensed under the MIT License.