from setuptools import setup, find_packages

setup(
    name="resume-extractor",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "gunicorn==20.1.0",
        "uvicorn==0.24.0",
        "python-multipart==0.0.6",
        "PyMuPDF==1.23.6",
        "python-dotenv==1.0.0",
        "motor==3.5.3",
        "pymongo==4.5.0",
        "python-jose[cryptography]==3.3.0",
        "passlib[bcrypt]==1.7.4",
        "nltk==3.8.1",
        "spacy==3.7.2",
        "pandas==2.0.3",
        "ratelimit==2.2.12",
        "httpx==0.25.1",
        "filetype>=1.2.0"
    ],
    python_requires='>=3.8',
)
