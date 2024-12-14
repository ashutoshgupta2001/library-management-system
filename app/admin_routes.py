from flask import Flask, request, jsonify
from .models import User, Book, BorrowRequest
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import app, db, bcrypt
import re
# Helper Functions
def is_admin():
    user_email = get_jwt_identity()
    if not user_email:
        return False 
    
    print(f"User email from token: {user_email}")
    user = User.query.filter_by(email=user_email).first()
    
    if user:
        return user.is_admin
    return False  


@app.route('/api/admin/create_user', methods=['POST'])
@jwt_required()
def create_user():
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403

    data = request.json
    email = data.get('email')
    password = data.get('password')
    admin_user = data.get('admin_user', False)

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, email):
        return jsonify({'error': 'Invalid email format'}), 400

    # Check if the email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'error': 'User with this email already exists'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(email=email, password=hashed_password, is_admin=admin_user)
    
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully', "user_id": new_user.id}), 201


@app.route('/api/admin/view_requests', methods=['GET'])
@jwt_required()
def view_requests():
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403

    requests = BorrowRequest.query.all()
    response = [
        {
            'id': req.id,
            'user_id': req.user_id,
            'book_id': req.book_id,
            'start_date': req.start_date,
            'end_date': req.end_date,
            'status': req.status
        } for req in requests
    ]
    return jsonify(response), 200

@app.route('/api/admin/handle_request/<int:request_id>', methods=['POST'])
@jwt_required()
def handle_request(request_id):
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403

    data = request.json
    status = data.get('status')
    if not status:
        return jsonify({'error': 'Missing Fields', "message": "status field is required"}), 400
    if status not in ['Approved', 'Denied']:
        return jsonify({'error': 'Invalid status', "message": "Status should be in ['Approved', 'Denied']"}), 400

    borrow_request = BorrowRequest.query.get(request_id)
    if not borrow_request:
        return jsonify({'error': 'Book borrow request not found'}), 404

    if status == 'Approved':
        book = Book.query.get(borrow_request.book_id)
        if not book.available:
            return jsonify({'error': 'Book is not available'}), 400
        book.available_qty -=1
        if book.available_qty == 0:
            book.available = False


    borrow_request.status = status
    db.session.commit()
    return jsonify({'message': f'Request {status} successfully'}), 200

@app.route('/api/admin/user_history/<int:user_id>', methods=['GET'])
@jwt_required()
def user_history(user_id):
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403

    requests = BorrowRequest.query.filter_by(user_id=user_id).all()
    response = [
        {
            'book_id': req.book_id,
            'start_date': req.start_date,
            'end_date': req.end_date,
            'status': req.status
        } for req in requests
    ]
    return jsonify(response), 200






