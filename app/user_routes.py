from flask import Flask, request, jsonify, Response
from .models import User, Book, BorrowRequest
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import app, db, bcrypt
from io import StringIO
import csv

# Routes
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    access_token = create_access_token(identity=user.email)
    return jsonify({'access_token': access_token, 'token_type':'Bearer'}), 200


# Library User APIs
@app.route('/api/books', methods=['GET'])
@jwt_required()
def get_books():
    books = Book.query.all()
    response = [
        {
            'id': book.id,
            'title': book.title,
            'available': book.available,
            'available_qty': book.available_qty
        } for book in books
    ]
    return jsonify(response), 200

@app.route('/api/book-request', methods=['POST'])
@jwt_required()
def borrow_book():
    data = request.json
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    user_id = user.id
    book_id = data.get('book_id')
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    if not all([book_id, start_date, end_date]):
        return jsonify({'error': 'All fields are required'}), 400

    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 400

    if not book.available:
        return jsonify({'error': 'Book is not available'}), 400

    overlapping_request = BorrowRequest.query.filter(
        BorrowRequest.book_id == book_id,
        BorrowRequest.status == 'Approved',
        BorrowRequest.start_date <= end_date,
        BorrowRequest.end_date >= start_date
    ).first()

    if overlapping_request:
        return jsonify({'error': 'Book is already borrowed for these dates'}), 400

    borrow_request = BorrowRequest(
        user_id=user_id,
        book_id=book_id,
        start_date=start_date,
        end_date=end_date
    )
    db.session.add(borrow_request)
    db.session.commit()
    return jsonify({'message': 'Borrow request submitted successfully'}), 201

@app.route('/api/user/history', methods=['GET'])
@jwt_required()
def personal_history():
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    user_id = user.id
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

@app.route('/api/user/download_history', methods=['GET'])
@jwt_required()
def download_history():
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    user_id = user.id
    requests = BorrowRequest.query.filter_by(user_id=user_id).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Book ID', 'Start Date', 'End Date', 'Status'])

    for req in requests:
        writer.writerow([req.book_id, req.start_date, req.end_date, req.status])

    output.seek(0)
    return Response(output.getvalue(),
                    mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=borrow_history.csv'})