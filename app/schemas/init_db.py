#!/usr/bin/env python3
"""
Database Initialization Script

This script initializes the SQLite database and populates it with 
products and reviews from the Kaggle dataset (1429_1.csv) if it is present.
"""

from app.database import initialize_database

if __name__ == "__main__":
    print("Starting database initialization...")
    initialize_database()
    print("Initialization finished.")
