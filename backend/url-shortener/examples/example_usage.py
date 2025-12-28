"""Example usage of URL Shortener API."""

import requests
import json

BASE_URL = "http://localhost:8000"


def create_short_url(original_url: str, custom_alias: str = None, expiration_time: str = None):
    """Create a short URL."""
    payload = {
        "original_url": original_url
    }
    
    if custom_alias:
        payload["custom_alias"] = custom_alias
    
    if expiration_time:
        payload["expiration_time"] = expiration_time
    
    response = requests.post(
        f"{BASE_URL}/urls",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Created short URL: {data['short_url']}")
        return data['short_url']
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None


def redirect_short_url(short_code: str):
    """Redirect to original URL (follow redirects)."""
    response = requests.get(
        f"{BASE_URL}/{short_code}",
        allow_redirects=True
    )
    
    print(f"Status: {response.status_code}")
    print(f"Final URL: {response.url}")
    return response


if __name__ == "__main__":
    print("=== URL Shortener Example ===\n")
    
    # Example 1: Create a simple short URL
    print("1. Creating a short URL...")
    short_url = create_short_url("https://www.example.com/very/long/path/to/resource")
    print()
    
    # Example 2: Create with custom alias
    print("2. Creating with custom alias...")
    custom_short = create_short_url(
        "https://www.google.com",
        custom_alias="google"
    )
    print()
    
    # Example 3: Create with expiration
    print("3. Creating with expiration...")
    from datetime import datetime, timedelta
    expiration = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
    expiring_short = create_short_url(
        "https://www.github.com",
        expiration_time=expiration
    )
    print()
    
    # Example 4: Test redirect
    if custom_short:
        print("4. Testing redirect...")
        short_code = custom_short.split("/")[-1]
        redirect_short_url(short_code)
        print()

