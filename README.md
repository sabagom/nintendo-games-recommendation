# Nintendo Games Rental and Recommendation System

A Python-based system for managing user registration, login, game rental, and personalized game recommendations using MongoDB and a Nintendo games dataset.

## Features

- User registration and login with secure password hashing (bcrypt)
- Game data ingestion from CSV file into MongoDB
- Personalized game recommendations:
  - By title similarity (using TF-IDF and Cosine Similarity)
  - By genre preference
- Game rental and return functionality
- Simple graphical interface using Pygame

## Technologies Used

- Python
- MongoDB
- Pandas
- Scikit-learn (TF-IDF, Cosine Similarity)
- bcrypt
- Pygame
