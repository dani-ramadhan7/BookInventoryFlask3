from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
# import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # SQLite database file
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Define Book and InventoryLog models
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(255), nullable=False)
    inventory_log = db.relationship('InventoryLog', backref='book', lazy=True, cascade="all, delete-orphan")

class InventoryLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity_change = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)

# db.create_all()

# # Sample data for books and inventory logs
# books = [
#     {
#         'id': 1,
#         'name': 'Book 1',
#         'author': 'Author 1',
#         'description': 'Description for Book 1',
#         'stock': 10,
#         'image': 'book1.jpg',
#         'inventory_log': []
#     },
#     {
#         'id': 2,
#         'name': 'Book 2',
#         'author': 'Author 2',
#         'description': 'Description for Book 2',
#         'stock': 15,
#         'image': 'book2.jpg',
#         'inventory_log': []
#     }
# ]

def get_inventory_levels():
    inventory_levels = {}
    for book in books:
        inventory_levels[book['name']] = book['stock']
    return inventory_levels

# @app.route('/')
# def home():
#     return render_template('index.html', books=books)

@app.route('/')
def home():
    books = Book.query.all()
    return render_template('index_bootstrap.html', books=books)

@app.route('/book/<int:book_id>')
def book_detail(book_id):
    book = Book.query.get(book_id)
    # book = next((b for b in books if b['id'] == book_id), None)
    if book:
        return render_template('book_detail.html', book=book)
    return 'Book not found', 404

# SQLite
@app.route('/book/<int:book_id>/edit_inventory', methods=['GET', 'POST'])
def edit_inventory(book_id):
    book = Book.query.get(book_id)
    if request.method == 'POST':
        quantity_change = int(request.form['quantity'])
        description = request.form['description']
        timestamp = datetime.utcnow()  # Use UTC time to match the default behavior in your model

        # Update the database record
        book.stock += quantity_change
        db.session.add(InventoryLog(quantity_change=quantity_change, description=description, timestamp=timestamp, book=book))
        db.session.commit()

        return redirect(url_for('book_detail', book_id=book_id))
    return render_template('edit_inventory.html', book=book)


# # Previous
# @app.route('/book/<int:book_id>/edit_inventory', methods=['GET', 'POST'])
# def edit_inventory(book_id):
#     book = Book.query.get(book_id)
#     # book = next((b for b in books if b['id'] == book_id), None)
#     if request.method == 'POST':
#         quantity_change = int(request.form['quantity'])
#         description = request.form['description']
#         timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#         book['stock'] += quantity_change
#         book['inventory_log'].append({'quantity_change': quantity_change, 'description': description, 'timestamp': timestamp})
#         return redirect(url_for('book_detail', book_id=book_id))
#     return render_template('edit_inventory.html', book=book)

@app.route('/inventory_log')
def inventory_log():
    all_logs = []
    for book in books:
        for log in book['inventory_log']:
            all_logs.append({'book_name': book['name'], 'quantity_change': log['quantity_change'], 'description': log['description'], 'timestamp': log['timestamp']})
    all_logs.sort(key=lambda x: x['timestamp'], reverse=True)
    return render_template('inventory_log.html', logs=all_logs)

# SQLite
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        new_book = Book(
            name=request.form['name'],
            author=request.form['author'],
            description=request.form['description'],
            stock=int(request.form['stock']),
            image=request.form['image']
        )
        db.session.add(new_book)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('add_book.html')

# # Previous
# @app.route('/add_book', methods=['GET', 'POST'])
# def add_book():
#     if request.method == 'POST':
#         new_book = {
#             'id': len(books) + 1,
#             'name': request.form['name'],
#             'author': request.form['author'],
#             'description': request.form['description'],
#             'stock': int(request.form['stock']),
#             'image': request.form['image'],
#             'inventory_log': []
#         }
#         books.append(new_book)
#         return redirect(url_for('home'))
#     return render_template('add_book.html')

@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    book = Book.query.get(book_id)
    if request.method == 'POST':
        book.name = request.form['name']
        book.author = request.form['author']
        book.description = request.form['description']
        book.stock = int(request.form['stock'])
        book.image = request.form['image']
        db.session.commit()
        return redirect(url_for('book_detail', book_id=book_id))
    return render_template('edit_book.html', book=book)

# # Previous
# @app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
# def edit_book(book_id):
#     book = next((b for b in books if b['id'] == book_id), None)
#     if request.method == 'POST':
#         book['name'] = request.form['name']
#         book['author'] = request.form['author']
#         book['description'] = request.form['description']
#         book['stock'] = int(request.form['stock'])
#         book['image'] = request.form['image']
#         return redirect(url_for('book_detail', book_id=book_id))
#     return render_template('edit_book.html', book=book)

@app.route('/delete_book/<int:book_id>')
def delete_book(book_id):
    book = Book.query.get(book_id)
    if book:
        # Delete associated logs
        InventoryLog.query.filter_by(book_id=book.id).delete()

        db.session.delete(book)
        db.session.commit()
    return redirect(url_for('home'))

# # Previous
# @app.route('/delete_book/<int:book_id>')
# def delete_book(book_id):
#     global books
#     books = [book for book in books if book['id'] != book_id]
#     return redirect(url_for('home'))

# @app.route('/levels')
# def inventory_levels():
#     inventory_levels_data = get_inventory_levels()
    
#     plt.figure(figsize=(8, 6))
#     plt.bar(inventory_levels_data.keys(), inventory_levels_data.values(), color='blue')
#     plt.title('Inventory Levels')
#     plt.xlabel('Books')
#     plt.ylabel('Stock')
#     plt.xticks(rotation=45, ha='right')
    
#     # Save the plot to a BytesIO object
#     image_stream = BytesIO()
#     plt.savefig(image_stream, format='png')
#     image_stream.seek(0)
    
#     # Encode the plot as base64 for embedding in HTML
#     image_base64 = base64.b64encode(image_stream.read()).decode('utf-8')
    
#     return render_template('inventory_levels.html', image_base64=image_base64)

if __name__ == '__main__':
    # db.create_all()
    app.run(debug=True)