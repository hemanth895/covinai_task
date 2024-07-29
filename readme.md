
Sure, here’s a step-by-step guide to set up and run a Flask app in a local environment:

Running a Flask App in a Local Environment
1. Install Python
Ensure Python is installed on your machine. You can check this by running:

bash
Copy code
python --version
If Python is not installed, download and install it from the official Python website.

2. Create a Virtual Environment
Navigate to the directory where you want to create your project and create a virtual environment:

bash
Copy code
cd path/to/your/project
python -m venv env
This creates a directory named env that will contain the virtual environment.

3. Activate the Virtual Environment
Activate the virtual environment:

On Windows:

bash
Copy code
.\env\Scripts\activate
On macOS/Linux:

bash
Copy code
source env/bin/activate
Your command line should now show (env) indicating that the virtual environment is active.

4. Install Flask
With the virtual environment activated, install Flask using pip:

bash
Copy code
pip install Flask
If you have additional dependencies, such as those listed in a requirements.txt file, you can install them with:

bash
Copy code
pip install -r requirements.txt
5. Set Up Your Flask Application
Create a new file named app.py (or whatever name you prefer) and add your Flask application code. For example:

python
Copy code
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, Flask!"

if __name__ == '__main__':
    app.run(debug=True)
6. Set Environment Variables (if needed)
If your Flask app requires environment variables (e.g., for configuration), set them in your terminal:

On Windows:

bash
Copy code
set FLASK_APP=app.py
set FLASK_ENV=development
On macOS/Linux:

bash
Copy code
export FLASK_APP=app.py
export FLASK_ENV=development
7. Run the Flask Application
With your environment set up and variables configured, run the Flask app using the flask command:

bash
Copy code
flask run
Alternatively, you can run the app directly using Python:

bash
Copy code
python app.py
8. Access the Application
Open your web browser and navigate to http://127.0.0.1:5000 to view your Flask application. You should see the message "Hello, Flask!" if you used the example code.

9. Stop the Application
To stop the Flask application, return to your terminal and press Ctrl+C.

10. Deactivate the Virtual Environment
Once you're done working, deactivate the virtual environment:

bash
Copy code
deactivate


Simple API Documentation
Base URL
arduino
Copy code
http://127.0.0.1:5000
Endpoints
User Authentication
1. Register User
Endpoint: /register
Method: POST
Description: Register a new user.
Request Body Example:
json
Copy code
{
  "email": "user@example.com",
  "name": "John Doe",
  "mobile": "+1234567890",
  "password": "securepassword"
}
Response Example:
json
Copy code
{
  "message": "User registered successfully"
}
2. Login
Endpoint: /login
Method: POST
Description: Log in a user and receive a JWT token.
Request Body Example:
json
Copy code
{
  "email": "user@example.com",
  "password": "securepassword"
}
Response Example:
json
Copy code
{
  "token": "your_jwt_token_here"
}
User Management
3. Create User
Endpoint: /users
Method: POST
Description: Create a new user (authentication required).
Request Body Example:
json
Copy code
{
  "email": "newuser@example.com",
  "name": "Jane Smith",
  "mobile": "+0987654321"
}
Response Example:
json
Copy code
{
  "message": "User created successfully"
}
4. Get User
Endpoint: /users/<int:user_id>
Method: GET
Description: Retrieve user details by ID (authentication required).
Response Example:
json
Copy code
{
  "email": "user@example.com",
  "name": "John Doe",
  "mobile": "+1234567890"
}
Expense Management
5. Add Expense
Endpoint: /expenses
Method: POST
Description: Add a new expense (authentication required).
Request Body Example:
json
Copy code
{
  "description": "Dinner at restaurant",
  "total_amount": 100.00,
  "created_by": 1,
  "split_type": "equal",
  "participants": [1, 2, 3]
}
Response Example:
json
Copy code
{
  "message": "Expense added successfully"
}
6. Get User Expenses
Endpoint: /users/<int:user_id>/expenses
Method: GET
Description: Get all expenses created by a user (authentication required).
Response Example:
json
Copy code
[
  {
    "description": "Dinner at restaurant",
    "total_amount": 100.00,
    "split_type": "equal"
  }
]
7. Get Overall Expenses
Endpoint: /expenses/overall
Method: GET
Description: Get the total amount of all expenses (authentication required).
Response Example:
json
Copy code
{
  "total_expenses": 250.00
}
Balance Sheet
8. Download Balance Sheet
Endpoint: /balance-sheet
Method: GET
Description: Download the balance sheet as a CSV file (authentication required).
Response: CSV file download
This simplified documentation provides a clear overview of the available endpoints, their methods, descriptions, and examples of request and response data.

I deplyed this app on AWS ec2 ubuntu vm with postgres rds  
u can access all endpoints at the below ip 
http://3.12.120.43:5000/   at this ip
