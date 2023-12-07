# 101 Trivia
## Video Demo: https://www.youtube.com/watch?v=saijNFYGfEU
## Describtion:
This project is a web application for a trivia game, where users can register, log in, and play trivia games in two modes: "Creative Game" and "Challenge Game." Users can also view a ranking of players based on their scores. The application is built using Flask, MySQL for the database, and the GPT-3 language model from OpenAI for generating trivia questions.

# Prerequisites
Before running the application, make sure you have the following dependencies and configurations in place:

Python 3.x installed
Flask framework installed
Flask Sessions
MySQL server installed and configured
An OpenAI API key for using the GPT-3 language model
A .env file containing the necessary environment variables

# Installation
Clone the repository:
git clone https://github.com/your/repository.git

Install the required Python packages:
pip install -r requirements.txt

Configure the database by modifying the db_config.py file with your MySQL credentials.

Set up your OpenAI API key in the .env file.

# Usage
To start the application, run the following command:
flask run

The application will be accessible at http://localhost:5000.

# Features
Registration and Login: Users can register for an account and log in to play the trivia games. Both routes are designed with help of jinja and HTML forms.
Both forms have error handling for doubling username, different password and repetition of the password or any form missing. If there are not any errors
user's input is included in database after earlier password hashing.

Creative Game: Users can input a topic, and the application will generate trivia questions related to that topic using the GPT-3 model. Users must answer these questions. It is made with OPEN AI API that gives access to GPT-3 model and after user writes one-word topic ai model generates output that is designed by code to
fit in HTML display of question. After user is redirected to form where question and answers are displayed. If user answers correctly 1 point is assinged to his/her account.

Challenge Game: Users can play a challenge game with pre-defined trivia questions. The application randomly selects questions from the database for users to answer.
I selected MySQL database with which I connect to store 120 records of trivia questions. Question is randomly selected to be answered and if user is correct one point
is added to user's account. User knows if he/she answered correctly by message flashing accessible in Flask framework.

Scoring: Users receive points for correct answers, and their scores are stored in the database.

Ranking: Users can view a ranking of players based on their scores. In that route Bootstrap table is displayed and with help of jinja
all registered users and their score are displayed.

Log out: This rout clears all session variables and log user out.
