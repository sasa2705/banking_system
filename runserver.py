#!/usr/bin/env python
import os
import subprocess

def main():
    """Start Django development server with debug settings"""
    print("Starting Django Banking System...")
    
    # Create database migrations if they don't exist
    print("Creating database migrations...")
    subprocess.run(["python", "manage.py", "makemigrations"])
    
    # Apply migrations
    print("Applying migrations...")
    subprocess.run(["python", "manage.py", "migrate"])
    
    # Initialize demo data
    try:
        print("Initializing demo data...")
        subprocess.run(["python", "init_data.py"])
    except Exception as e:
        print(f"Warning: Could not initialize data: {e}")
    
    # Start server
    print("Starting development server...")
    subprocess.run(["python", "manage.py", "runserver", "0.0.0.0:8000"])

if __name__ == "__main__":
    main() 