# Resume Skill Extractor

An end-to-end web application that extracts structured data from PDF resumes using NLP techniques.

## Features

- Upload PDF resumes
- Extract structured data (name, email, phone, skills, experience)
- Filter resumes by skills
- View detailed resume information
- Responsive design

## Tech Stack

- Frontend: React + TailwindCSS
- Backend: FastAPI (Python)
- Database: MongoDB
- PDF Parsing: PyMuPDF
- NLP: spaCy

## Setup Instructions

### Backend Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install spaCy model:
```bash
python -m spacy download en_core_web_sm
```

3. Run the backend server:
```bash
uvicorn server.main:app --reload
```

### Frontend Setup

1. Navigate to the client directory:
```bash
cd client
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

### MongoDB Setup

You can use either:
1. Local MongoDB installation
2. MongoDB Atlas (recommended for production)

If using MongoDB Atlas:
1. Create a new cluster
2. Add your IP address to the whitelist
3. Create a database user
4. Update the `.env` file with your connection string

### Environment Variables

Create a `.env` file in the root directory with the following:
```
MONGODB_URI=mongodb://localhost:27017
```

## API Endpoints

- POST `/upload` - Upload a PDF resume
- GET `/resumes` - Get list of all resumes
- GET `/resumes/{id}` - Get specific resume details

## Project Structure

```
resume-extractor/
├── client/         # React frontend
├── server/         # FastAPI backend
├── requirements.txt # Python dependencies
└── README.md
```

## Usage

1. Start both frontend and backend servers
2. Navigate to `http://localhost:3000`
3. Upload a PDF resume
4. View extracted information and filter by skills

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License
