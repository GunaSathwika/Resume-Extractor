# Resume Extractor

A full-stack application for extracting skills and information from resumes using FastAPI and React.

## Features

- Resume upload and processing
- Skill extraction using Spacy
- Modern React frontend
- RESTful API backend
- MongoDB database integration
- Prometheus monitoring
- Rate limiting and security features

## Tech Stack

- Frontend: React
- Backend: FastAPI
- Database: MongoDB
- NLP: Spacy
- Monitoring: Prometheus
- Deployment: Render

## Project Structure

```
resume-extractor/
├── client/                 # React frontend
│   ├── public/            # Static assets
│   └── src/               # Source code
│       ├── components/    # React components
│       ├── pages/         # Page components
│       ├── services/      # API services
│       └── App.js         # Main application
├── server/                # FastAPI backend
│   ├── app/              # FastAPI application
│   │   ├── main.py       # Main application
│   │   ├── models/       # Pydantic models
│   │   └── routes/       # API routes
│   └── tests/            # Test files
├── .env                  # Environment variables
├── requirements.txt      # Python dependencies
├── setup.py              # Python package setup
└── README.md            # Documentation
```

## Setup Instructions

### Prerequisites

- Python 3.10+
- Node.js 16+
- MongoDB
- Git

### Backend Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Run the backend:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. Install Node dependencies:
   ```bash
   cd client
   npm install
   ```

2. Run the frontend:
   ```bash
   npm start
   ```

### Deployment

The application is configured for deployment on Render.com. The deployment configuration is in:

- `server/render.toml` - Main deployment configuration
- `server/render.yaml` - Alternative deployment configuration

### Monitoring

The application includes Prometheus monitoring with the following metrics:

- Request counts
- Request latency
- Resume downloads
- Error tracking

Access metrics at `/metrics` endpoint.

## Security Features

- Rate limiting
- HTTPS enforcement
- Secure headers
- Session management
- CORS configuration
- Environment variable based configuration

## API Documentation

The API is documented using FastAPI's automatic documentation. Access it at:

- Swagger UI: `/docs`
- ReDoc: `/redoc`

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
