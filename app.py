from datetime import datetime,timedelta
from flask import Flask, request, jsonify, abort
from models import ExpenseParticipant, db, User, Expense
import jwt
#from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from dotenv import load_dotenv
import os
from flask_bcrypt import Bcrypt
import pandas as pd
from io import StringIO,BytesIO
from flask import send_file



bcrypt = Bcrypt()





app = Flask(__name__)

# Update the database URI to connect to PostgreSQL

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')

# below one is for production
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:hemanth017049@covinaitaskdb.c5m8em6amu3d.us-east-2.rds.amazonaws.com:5432/covinaitaskdb'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

load_dotenv()

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['ALGORITHMS'] = os.getenv('ALGORITHMS')


db.init_app(app)


#@app.before_first_request
#def create_tables():
#    db.create_all()


# Ensure tables are created when the application starts
with app.app_context():
    db.create_all()
    
    
# auth middleware i implemented as decorator func:
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
          # Bearer token format, so we need to split and get the token part
        if token.startswith('Bearer '):
            token = token.split('Bearer ')[1]
        else:
            return jsonify({'message': 'Token format is incorrect!'}), 403
        
        
        print("token  -- "+ token)


        try:
            print("secret key"+app.config['SECRET_KEY'])
            print("alogritms "+app.config['ALGORITHMS'])

            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms= app.config['ALGORITHMS'])
            current_user = User.query.filter_by(id=data['user_id']).first()
            #current_user = User.query.get(1)  # Retrieve user using primary key

        except:
            return jsonify({'message': 'Token is invalid!'}), 403
        
        return f(current_user, *args, **kwargs)

    return decorated

    
    
    
#authentication endpoints
    
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User already exists'}), 409

    # Hash the password using bcrypt
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    # Create a new user object
    new_user = User(
        email=data['email'],
        name=data['name'],
        mobile=data['mobile'],
        password_hash=hashed_password
    )

    # Add and commit the new user to the database
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()

    if user is None:
        return jsonify({'message': 'Invalid credentials'}), 401

    # Debugging: Print the hashed password from the database
    print(f"Stored hash: {user.password_hash}")

    # Check if the password is correct
    try:
        if not bcrypt.check_password_hash(user.password_hash, data['password']):
            return jsonify({'message': 'Invalid credentials'}), 401
    except ValueError as e:
        print(f"Error: {e}")
        return jsonify({'message': 'Invalid salt in stored password hash'}), 500

    # Generate JWT token
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({'token': token})




#user endpoints
    
@app.route("/",methods=['GET'])
def helloworld():
    return jsonify({"message":"hello world"})

#create user endpoint


@app.route('/users', methods=['POST'])
@token_required
def create_user(current_user):
    data = request.get_json()
    new_user = User(email=data['email'], name=data['name'], mobile=data['mobile'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/users/<int:user_id>', methods=['GET'])
@token_required
def get_user(current_user,user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({'email': user.email, 'name': user.name, 'mobile': user.mobile})


#expenses endpoints

# Expense endpoints
@app.route('/expenses', methods=['POST'])
@token_required
def add_expense(current_user):
    data = request.get_json()
    
    try:
        description = data['description']
        total_amount = data['total_amount']
        created_by = data['created_by']
        split_type = data['split_type']
        participants = data['participants']
    except KeyError as e:
        return jsonify({'message': f'Missing required field: {e.args[0]}'}), 400
    
    # Create a new expense record
    new_expense = Expense(description=description, total_amount=total_amount, created_by=created_by, split_type=split_type)
    db.session.add(new_expense)
    db.session.commit()
    
    expense_id = new_expense.id
    
    # Calculate the amount each participant owes based on the split_type
    if split_type == 'equal':
        amount_per_person = total_amount / len(participants)
        for user_id in participants:
            new_participant = ExpenseParticipant(expense_id=expense_id, user_id=user_id, amount_owed=amount_per_person)
            db.session.add(new_participant)
    
    elif split_type == 'exact':
        # Assuming split_method is a dictionary for exact amounts
        exact_amounts = data.get('split_method', {})
        for participant in participants:
            amount_owed = exact_amounts.get(participant, 0)
            new_participant = ExpenseParticipant(expense_id=expense_id, user_id=participant, amount_owed=amount_owed)
            db.session.add(new_participant)
    
    elif split_type == 'percentage':
        # Assuming split_method is a dictionary for percentages
        percentages = data.get('split_method', {})
        for participant in participants:
            percentage = percentages.get(participant, 0)
            amount_owed = (percentage / 100) * total_amount
            new_participant = ExpenseParticipant(expense_id=expense_id, user_id=participant, amount_owed=amount_owed)
            db.session.add(new_participant)
    
    db.session.commit()
    return jsonify({'message': 'Expense added successfully'}), 201




@app.route('/users/<int:user_id>/expenses', methods=['GET'])
@token_required
def get_user_expenses(current_user, user_id):
    user = User.query.get_or_404(user_id)
    expenses = Expense.query.filter_by(created_by=user.id).all()
    result = [{'description': expense.description, 'total_amount': expense.total_amount, 'split_type': expense.split_type} for expense in expenses]
    return jsonify(result)




@app.route('/expenses/overall', methods=['GET'])
@token_required
def get_overall_expenses(current_user):
    expenses = Expense.query.all()
    total_expenses = sum(expense.total_amount for expense in expenses)
    return jsonify({'total_expenses': total_expenses})



from flask import send_file
from io import StringIO

from flask import send_file, jsonify
from io import BytesIO

@app.route('/balance-sheet', methods=['GET'])
@token_required
def download_balance_sheet(current_user):
    try:
        # Call the function to generate the balance sheet
        balance_sheet_csv = generate_balance_sheet()

        # Ensure it's a valid file-like object
        if not isinstance(balance_sheet_csv, BytesIO):
            return jsonify({'message': 'Error generating balance sheet'}), 500

        # Send the file as a response
        return send_file(
            balance_sheet_csv,
            mimetype='text/csv',
            as_attachment=True,
            download_name='balance_sheet.csv'  # For Flask 2.0 and newer
        )

    except Exception as e:
        return jsonify({'message': str(e)}), 500






def generate_balance_sheet():
    # Query all expenses and participants
    expenses = Expense.query.all()
    participants_balances = {}

    for expense in expenses:
        participants = ExpenseParticipant.query.filter_by(expense_id=expense.id).all()
        total_amount = expense.total_amount

        if len(participants) == 0:
            continue  # Skip expenses with no participants

        if expense.split_type == 'equal':
            amount_per_person = total_amount / len(participants)
            for participant in participants:
                user_id = participant.user_id
                if user_id not in participants_balances:
                    participants_balances[user_id] = 0
                participants_balances[user_id] -= amount_per_person

        elif expense.split_type == 'exact':
            for participant in participants:
                user_id = participant.user_id
                amount_owed = participant.amount_owed
                if user_id not in participants_balances:
                    participants_balances[user_id] = 0
                participants_balances[user_id] -= amount_owed

        elif expense.split_type == 'percentage':
            for participant in participants:
                user_id = participant.user_id
                amount_owed = (participant.amount_owed / total_amount) * 100
                if user_id not in participants_balances:
                    participants_balances[user_id] = 0
                participants_balances[user_id] -= amount_owed

    # Convert balances to a DataFrame
    data = [{'user_id': user_id, 'balance': balance} for user_id, balance in participants_balances.items()]
    df = pd.DataFrame(data)

    # Generate CSV
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)

    return output


    


if __name__ == '__main__':
    app.run(debug=True)
