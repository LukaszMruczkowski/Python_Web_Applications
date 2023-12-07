# 101 Trivia
## Description:
This project is a web application for a trivia game, where users can register, log in, and play trivia games in two modes: "Creative Game" and "Challenge Game." Users can also view a ranking of players based on their scores. The application uses Flask, MySQL for the database and the GPT-3 language model from OpenAI for generating trivia questions.

# Features
Registration and Login: Users can register for an account and log in to play the trivia games. Both routes are designed with the help of jinja and HTML forms.
Both forms have error handling for doubling username, different password, and repetition of the password or any form missing. If there are not any errors
user's input is included in the database after earlier password hashing.

Creative Game: Users can input a topic, and the application will generate trivia questions related to that topic using the GPT-3 model. Users must answer these questions. It is made with OPEN AI API that gives access to GPT-3 model and after the user writes a one-word topic ai model generates output designed by code to
fit in the HTML display of the question. After a user is redirected to the form where questions and answers are displayed. If the user answers correctly 1 point is assigned to his/her account.

Challenge Game: Users can play a challenge game with pre-defined trivia questions. The application randomly selects questions from the database for users to answer.
I selected the MySQL database with which I connect to store 120 records of trivia questions. The question is randomly selected to be answered and if a user is correct one point
is added to the user's account. The user knows if he/she answered correctly by message flashing accessible in the Flask framework.

Scoring: Users receive points for correct answers, and their scores are stored in the database.

Ranking: Users can view a ranking of players based on their scores. In that route, the Bootstrap table is displayed and with the help of Jinja
all registered users and their scores are displayed.

Log out: This route clears all session variables and logs a user out.
