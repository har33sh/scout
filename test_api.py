#!/usr/bin/env python3
"""
Test script for the Profile Scout API.
Run this script to test the /profiles endpoint with sample data.
"""

import asyncio
import json
import httpx

async def test_profiles_endpoint():
    """Test the /profiles endpoint with sample text"""
    
    # Sample text containing mentions of people and their roles
    sample_texts = [
        "John Smith is the CEO of TechCorp and leads a team of 50 engineers. Sarah Johnson works as a senior data scientist at Microsoft and has published several papers on machine learning.",
        
        "The keynote speaker was Dr. Michael Chen, a professor at Stanford University who specializes in artificial intelligence. Also presenting was Lisa Rodriguez, the CTO of StartupXYZ.",
        
        "Our advisory board includes former Google executive David Kim and renowned venture capitalist Emma Watson from Acme Ventures."
    ]
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test health endpoint first
        print("🔍 Testing health endpoint...")
        try:
            health_response = await client.get(f"{base_url}/health")
            print(f"Health Status: {health_response.status_code}")
            print(f"Health Data: {health_response.json()}\n")
        except Exception as e:
            print(f"❌ Error connecting to API: {e}")
            print("Make sure the server is running with: python main.py\n")
            return
        
        # Test profiles endpoint with each sample text
        for i, text in enumerate(sample_texts, 1):
            print(f"🔍 Test {i}: Processing text sample...")
            print(f"Input text: {text[:100]}...\n")
            
            try:
                response = await client.post(
                    f"{base_url}/profiles",
                    json={"text": text},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    profiles = result.get("profiles", [])
                    
                    print(f"✅ Found {len(profiles)} profiles:")
                    for profile in profiles:
                        print(f"  👤 {profile['name']}")
                        if profile.get('title'):
                            print(f"     💼 {profile['title']}")
                        print(f"     🔗 {profile['url']}")
                        print()
                else:
                    print(f"❌ Error {response.status_code}: {response.text}")
                    
            except Exception as e:
                print(f"❌ Error processing request: {e}")
            
            print("-" * 80)

async def test_invalid_input():
    """Test API with invalid input"""
    print("\n🔍 Testing with invalid input...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test with empty text
            response = await client.post(
                "http://localhost:8000/profiles",
                json={"text": ""},
                headers={"Content-Type": "application/json"}
            )
            print(f"Empty text response: {response.status_code}")
            
            # Test with missing field
            response = await client.post(
                "http://localhost:8000/profiles",
                json={},
                headers={"Content-Type": "application/json"}
            )
            print(f"Missing field response: {response.status_code}")
            
        except Exception as e:
            print(f"Error in invalid input test: {e}")

if __name__ == "__main__":
    print("🚀 Starting Profile Scout API Tests\n")
    print("Make sure the API server is running with: python main.py")
    print("=" * 80)
    
    # Run the tests
    asyncio.run(test_profiles_endpoint())
    asyncio.run(test_invalid_input())
    
    print("\n✅ Tests completed!")