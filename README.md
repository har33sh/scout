# Scout - Profile Extraction API

A FastAPI application that extracts professional profiles from raw text using LLM-powered keyword extraction and web search.

## Features

- **Text Analysis**: Uses OpenRouter LLM to extract people-related keywords from raw text
- **Web Search**: Leverages SerpAPI (Bing) to find relevant profiles
- **Smart Filtering**: Focuses on professional profile domains (LinkedIn, GitHub, Crunchbase, etc.)
- **Profile Extraction**: Extracts names and titles from profile pages
- **Deduplication**: Removes duplicate profiles based on name and URL similarity
- **Async Processing**: Fully asynchronous for high performance

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd scout
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Configuration

You'll need API keys for:
- **OpenRouter**: Get your key from [openrouter.ai](https://openrouter.ai)
- **SerpAPI**: Get your key from [serpapi.com](https://serpapi.com)

Add these to your `.env` file:
```
OPENROUTER_API_KEY=your_openrouter_api_key_here
SERPAPI_API_KEY=your_serpapi_key_here
```

## Usage

### Option 1: Direct Python
```bash
python main.py
```

### Option 2: Using the startup script
```bash
./run.sh
```

### Option 3: Using Docker
```bash
# Build and run with docker-compose
docker-compose up --build

# Or build and run manually
docker build -t profile-scout .
docker run -p 8000:8000 --env-file .env profile-scout
```

The API will be available at `http://localhost:8000`

### Interactive API Documentation
FastAPI automatically generates interactive documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Testing the API

1. **Using the test script:**
```bash
python test_api.py
```

2. **Manual curl request:**
```bash
curl -X POST "http://localhost:8000/profiles" \
     -H "Content-Type: application/json" \
     -d '{"text": "John Smith is a software engineer at Google and Jane Doe works as a product manager at Microsoft."}'
```

## API Endpoints

### POST /profiles
Extract professional profiles from text.

**Request Body:**
```json
{
  "text": "Your raw text containing people mentions"
}
```

**Response:**
```json
{
  "profiles": [
    {
      "name": "John Smith",
      "title": "Software Engineer at Google", 
      "url": "https://linkedin.com/in/johnsmith"
    },
    {
      "name": "Jane Doe",
      "title": "Product Manager",
      "url": "https://github.com/janedoe"
    }
  ]
}
```

### GET /health
Check API health and configuration status.

## Supported Profile Domains

- LinkedIn
- GitHub  
- Crunchbase
- Twitter
- Medium
- About.me
- Xing
- AngelList/Wellfound
- Dribbble
- Behance
- Stack Overflow
- Personal websites (basic heuristic detection)

## License

This project is open source and available under the [MIT License](LICENSE). 