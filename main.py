import asyncio
import json
import re
from typing import List, Optional, Dict, Set
from urllib.parse import urlparse

import aiohttp
import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Profile Scout API", version="1.0.0")

class TextInput(BaseModel):
    text: str

class ProfileResult(BaseModel):
    name: str
    title: Optional[str] = None
    url: str

class ProfilesResponse(BaseModel):
    profiles: List[ProfileResult]

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")

# Professional profile domains
PROFILE_DOMAINS = {
    'linkedin.com',
    'crunchbase.com', 
    'github.com',
    'twitter.com',
    'medium.com',
    'about.me',
    'xing.com',
    'angel.co',
    'wellfound.com',
    'dribbble.com',
    'behance.net',
    'stackoverflow.com'
}

async def extract_keywords_with_openrouter(text: str) -> List[str]:
    """Extract people-related search keywords using OpenRouter LLM"""
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenRouter API key not configured")
    
    prompt = f"""
    Extract people-related search keywords from the following text. Focus on:
    - Person names mentioned
    - Job titles or roles
    - Companies or organizations associated with people
    - Professional skills or expertise areas mentioned with people
    
    Return only the most relevant search terms that would help find professional profiles of people mentioned, separated by commas.
    
    Text: {text}
    
    Keywords:"""
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "anthropic/claude-3-haiku",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 200,
            "temperature": 0.3
        }
        
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        ) as response:
            if response.status != 200:
                raise HTTPException(status_code=500, detail=f"OpenRouter API error: {response.status}")
            
            result = await response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Parse keywords from response
            keywords = [k.strip() for k in content.split(',') if k.strip()]
            return keywords[:10]  # Limit to top 10 keywords

async def search_with_serpapi(keywords: List[str]) -> List[str]:
    """Search for keywords using SerpAPI and return URLs"""
    if not SERPAPI_KEY:
        raise HTTPException(status_code=500, detail="SerpAPI key not configured")
    
    all_urls = []
    
    async with aiohttp.ClientSession() as session:
        for keyword in keywords[:5]:  # Limit to top 5 keywords to avoid rate limits
            params = {
                "engine": "bing",
                "q": f"{keyword} profile OR linkedin OR github",
                "api_key": SERPAPI_KEY,
                "num": 20
            }
            
            async with session.get(
                "https://serpapi.com/search.json",
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    organic_results = data.get("organic_results", [])
                    
                    for result in organic_results:
                        url = result.get("link")
                        if url:
                            all_urls.append(url)
    
    return all_urls

def is_profile_domain(url: str) -> bool:
    """Check if URL is from a professional profile domain"""
    try:
        domain = urlparse(url).netloc.lower()
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Check if domain or any subdomain matches our profile domains
        for profile_domain in PROFILE_DOMAINS:
            if domain == profile_domain or domain.endswith(f'.{profile_domain}'):
                return True
        
        # Also check for personal domains (simple heuristic)
        # Personal sites often have patterns like firstname-lastname.com or firstnamelastname.com
        if any(char in domain for char in ['-', '_']) and '.' in domain:
            parts = domain.split('.')
            if len(parts) == 2 and len(parts[0]) > 5:  # Basic heuristic for personal domains
                return True
                
        return False
    except:
        return False

async def extract_profile_info(url: str) -> Optional[ProfileResult]:
    """Extract name and title from a profile URL"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, follow_redirects=True)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to extract name and title based on common patterns
            name = None
            title = None
            
            # LinkedIn specific extraction
            if 'linkedin.com' in url:
                name_elem = soup.find('h1', class_=re.compile(r'text-heading-xlarge|break-words'))
                if name_elem:
                    name = name_elem.get_text(strip=True)
                
                title_elem = soup.find('div', class_=re.compile(r'text-body-medium|break-words'))
                if title_elem:
                    title = title_elem.get_text(strip=True)
            
            # GitHub specific extraction
            elif 'github.com' in url:
                name_elem = soup.find('span', class_='p-name')
                if name_elem:
                    name = name_elem.get_text(strip=True)
                
                bio_elem = soup.find('div', class_='p-note')
                if bio_elem:
                    title = bio_elem.get_text(strip=True)
            
            # Generic extraction fallbacks
            if not name:
                # Try common title tag patterns
                title_tag = soup.find('title')
                if title_tag:
                    title_text = title_tag.get_text(strip=True)
                    # Extract name from title (common pattern: "Name - Title" or "Name | Company")
                    if ' - ' in title_text:
                        name = title_text.split(' - ')[0].strip()
                    elif ' | ' in title_text:
                        name = title_text.split(' | ')[0].strip()
                    elif len(title_text.split()) <= 4:  # Likely just a name
                        name = title_text
            
            # Try meta description for title/bio
            if not title:
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc and hasattr(meta_desc, 'get'):
                    title = meta_desc.get('content', '')[:100]  # Limit length
            
            # If we have at least a name, return the profile
            if name and len(name.strip()) > 0:
                return ProfileResult(
                    name=name.strip(),
                    title=title.strip() if title and isinstance(title, str) else None,
                    url=url
                )
            
            return None
            
    except Exception as e:
        print(f"Error extracting profile from {url}: {e}")
        return None

def deduplicate_profiles(profiles: List[ProfileResult]) -> List[ProfileResult]:
    """Remove duplicate profiles based on name similarity and URL"""
    seen_urls = set()
    seen_names = set()
    unique_profiles = []
    
    for profile in profiles:
        # Normalize URL for comparison
        normalized_url = profile.url.lower().rstrip('/')
        
        # Normalize name for comparison
        normalized_name = re.sub(r'[^\w\s]', '', profile.name.lower()).strip()
        
        if normalized_url not in seen_urls and normalized_name not in seen_names:
            seen_urls.add(normalized_url)
            seen_names.add(normalized_name)
            unique_profiles.append(profile)
    
    return unique_profiles

@app.post("/profiles", response_model=ProfilesResponse)
async def extract_profiles(input_data: TextInput):
    """
    Extract professional profiles from raw text.
    
    Process:
    1. Extract people-related keywords using OpenRouter LLM
    2. Search for those keywords using SerpAPI
    3. Filter URLs for professional profile domains
    4. Extract profile information (name, title, URL)
    5. Deduplicate and return results
    """
    try:
        # Step 1: Extract keywords using OpenRouter
        keywords = await extract_keywords_with_openrouter(input_data.text)
        
        if not keywords:
            return ProfilesResponse(profiles=[])
        
        # Step 2: Search with SerpAPI
        urls = await search_with_serpapi(keywords)
        
        # Step 3: Filter for profile domains
        profile_urls = [url for url in urls if is_profile_domain(url)][:20]  # Limit to top 20
        
        # Step 4: Extract profile information concurrently
        tasks = [extract_profile_info(url) for url in profile_urls]
        profile_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        valid_profiles = [
            result for result in profile_results 
            if isinstance(result, ProfileResult)
        ]
        
        # Step 5: Deduplicate
        unique_profiles = deduplicate_profiles(valid_profiles)
        
        return ProfilesResponse(profiles=unique_profiles)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Profile Scout API is running"}

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "openrouter_configured": bool(OPENROUTER_API_KEY),
        "serpapi_configured": bool(SERPAPI_KEY)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)