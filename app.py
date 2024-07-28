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
from io import StringIO
from flask import send_file



bcrypt = Bcrypt()





app = Flask(__name__)

# Update the database URI to connect to PostgreSQL

#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:root@127.0.0.1:5432/covinAI'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:hemanth017049@covinaitaskdb.c5m8em6amu3d.us-east-2.rds.amazonaws.com:5432/covinaitaskdb'

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
    print(data)
    #hashed_password = bcrypt.generate_password_hash(data['password'], method='sha256')
    hashed_password = bcrypt.generate_password_hash(data['password'])

    new_user = User(email=data['email'], name=data['name'], mobile=data['mobile'], password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if user is None:
        return jsonify({'message': 'Invalid credentials'}), 401

    # Check if the password is correct
    if not bcrypt.check_password_hash(user.password_hash, data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401

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

@app.route('/expenses', methods=['POST'])
def add_expense():
    data = request.get_json()
    description = data['description']
    total_amount = data['total_amount']
    created_by = data['created_by']
    split_type = data['split_type']
    participants = data['participants']

    new_expense = Expense(description=description, total_amount=total_amount, created_by=created_by, split_type=split_type)
    db.session.add(new_expense)
    db.session.commit()

    expense_id = new_expense.id

    if split_type == 'equal':
        amount_per_person = total_amount / len(participants)
        for user_id in participants:
            new_participant = ExpenseParticipant(expense_id=expense_id, user_id=user_id, amount_owed=amount_per_person)
            db.session.add(new_participant)
    elif split_type == 'exact':
        for participant in participants:
            new_participant = ExpenseParticipant(expense_id=expense_id, user_id=participant['user_id'], amount_owed=participant['amount_owed'])
            db.session.add(new_participant)
    elif split_type == 'percentage':
        for participant in participants:
            amount_owed = (participant['percentage'] / 100) * total_amount
            new_participant = ExpenseParticipant(expense_id=expense_id, user_id=participant['user_id'], amount_owed=amount_owed)
            db.session.add(new_participant)
    
    db.session.commit()
    return jsonify({'message': 'Expense added successfully'}), 201

@app.route('/users/<int:user_id>/expenses', methods=['GET'])
@token_required
def get_user_expenses(current_user,user_id):
    user = User.query.get_or_404(user_id)
    expenses = user.expenses
    result = []
    for expense in expenses:
        result.append({
            'description': expense.description,
            'total_amount': expense.total_amount,
            'split_method': expense.split_method
        })
    return jsonify(result)


@app.route('/expenses/overall', methods=['GET'])
@token_required
def get_overall_expenses(current_user):
    expenses = Expense.query.all()
    total_expenses = sum(expense.total_amount for expense in expenses)
    return jsonify({'total_expenses': total_expenses})

@app.route('/balance-sheet', methods=['GET'])
@token_required
def download_balance_sheet():
    # Call the function to generate the balance sheet
    balance_sheet = generate_balance_sheet()
    # Logic to download the balance sheet as a file
    return jsonify({
        "message":"balance sheet"
    })




def generate_balance_sheet():
    # Query all expenses and participants
    expenses = Expense.query.all()
    participants_balances = {}

    for expense in expenses:
        participants = ExpenseParticipant.query.filter_by(expense_id=expense.id).all()
        total_amount = expense.total_amount

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
    output = StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    return output

    


if __name__ == '__main__':
    app.run(debug=True)
