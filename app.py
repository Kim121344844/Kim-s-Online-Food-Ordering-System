import os
import uuid
import requests
import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit, join_room
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key
socketio = SocketIO(app)

# Payment API functions

def initiate_gcash_payment(amount, order_id, description):
    gcash_app_id = os.getenv('GCASH_APP_ID')
    gcash_app_secret = os.getenv('GCASH_APP_SECRET')
    # Mock GCash API call (replace with real API)
    # In production, use actual GCash API endpoints
    return {'status': 'success', 'payment_id': f'gcash_{order_id}', 'redirect_url': f'https://gcash.com/pay/{order_id}'}

def initiate_paymaya_payment(amount, order_id, description):
    paymaya_public_key = os.getenv('PAYMAYA_PUBLIC_KEY')
    paymaya_secret_key = os.getenv('PAYMAYA_SECRET_KEY')
    # Mock PayMaya API call (replace with real API)
    # In production, use actual PayMaya API endpoints
    return {'status': 'success', 'payment_id': f'paymaya_{order_id}', 'redirect_url': f'https://paymaya.com/pay/{order_id}'}

@app.context_processor
def inject_users():
    return {'users': users}

# Temporary in-memory user storage (replace with database later)
users = [
    {'name': 'Admin', 'email': 'admin@admin.com', 'password': 'admin123', 'role': 'admin'},
    {'name': 'John Doe', 'email': 'john@example.com', 'password': 'password123', 'role': 'user'},
    {'name': 'Jane Smith', 'email': 'jane@example.com', 'password': 'password123', 'role': 'user'},
    {'name': 'Alice Johnson', 'email': 'alice@example.com', 'password': 'password123', 'role': 'user'},
    {'name': 'Bob Brown', 'email': 'bob@example.com', 'password': 'password123', 'role': 'user'}
]

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/menu')
def menu():
    return render_template('menu.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']
        if len(password) < 6:
            return render_template('login.html', error='Password length is incorrect. Minimum 6 characters required.', email=email)
        # Find user by email
        user = next((u for u in users if u['email'] == email), None)
        if user:
            if user['password'] == password:
                session['user'] = email
                if user.get('role') == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error='Password is incorrect.', email=email)
        else:
            return render_template('login.html', error='Email not registered.', email=email)
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    user_email = session.get('user')
    if user_email:
        # Find user name from registered users
        user = next((u for u in users if u['email'] == user_email), None)
        user_name = user['name'] if user else 'User'  # Default to 'User' if not found
    else:
        user_name = 'Guest'
        user_email = 'guest@example.com'
    favorites = [
        {'name': 'Burger', 'image': 'images/Burger.jpg'},
        {'name': 'Pizza', 'image': 'images/Pizza.jpg'}
    ]
    cart = session.get('cart', [])
    return render_template('dashboard.html', user_name=user_name, user_email=user_email, favorites=favorites, cart=cart)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email'].lower()
        password = request.form['password']
        if len(password) < 6:
            return render_template('signup.html', error='Password length is incorrect. Minimum 6 characters required.', name=name, email=email)
        # Check if user already exists
        if any(user['email'] == email for user in users):
            return render_template('signup.html', error='Email already registered', name=name, email=email)
        # Save user (temporary in-memory storage)
        users.append({'name': name, 'email': email, 'password': password, 'role': 'user'})
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if 'user' not in session:
        return redirect(url_for('login', error='You are not logged in.'))
    if request.method == 'POST':
        session.pop('user', None)
        return redirect(url_for('home'))
    return render_template('logout_confirm.html')

@app.route('/add_item', methods=['POST'])
def add_item():
    item_name = request.form['item_name']
    item_price = float(request.form['item_price'])
    cart = session.get('cart', [])
    cart.append({'name': item_name, 'price': item_price})
    session['cart'] = cart
    return redirect(url_for('dashboard'))

@app.route('/remove_item/<int:index>')
def remove_item(index):
    cart = session.get('cart', [])
    if 0 <= index < len(cart):
        cart.pop(index)
        session['cart'] = cart
    return redirect(url_for('dashboard'))

@app.route('/add_item_payment', methods=['POST'])
def add_item_payment():
    item_name = request.form['item_name']
    item_price = float(request.form['item_price'])
    cart = session.get('cart', [])
    cart.append({'name': item_name, 'price': item_price})
    session['cart'] = cart
    return {'success': True, 'cart': cart, 'total': sum(item['price'] for item in cart)}

@app.route('/edit_item_payment/<int:index>', methods=['POST'])
def edit_item_payment(index):
    cart = session.get('cart', [])
    if 0 <= index < len(cart):
        item_name = request.form['item_name']
        item_price = float(request.form['item_price'])
        cart[index] = {'name': item_name, 'price': item_price}
        session['cart'] = cart
    return {'success': True, 'cart': cart, 'total': sum(item['price'] for item in cart)}

@app.route('/remove_item_payment/<int:index>', methods=['POST'])
def remove_item_payment(index):
    cart = session.get('cart', [])
    if 0 <= index < len(cart):
        cart.pop(index)
        session['cart'] = cart
    return {'success': True, 'cart': cart, 'total': sum(item['price'] for item in cart)}

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if 'user' not in session:
        return redirect(url_for('login'))
    cart = session.get('cart', [])
    if not cart:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        payment_method = request.form['payment_method']
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        postal = request.form.get('postal')
        city = request.form.get('city')
        if not email or not phone or not address or not postal or not city:
            return render_template('payment.html', cart=cart, error='Please provide email, phone, home address, postal number, and city for all payment methods.')
        total = sum(item['price'] for item in cart)
        order_id = str(uuid.uuid4())
        description = f"Order {order_id} for {session.get('user')}"

        if payment_method == 'GCash':
            payment_response = initiate_gcash_payment(total, order_id, description)
            if payment_response['status'] == 'success':
                status = 'Processing'
                payment_id = payment_response['payment_id']
            else:
                return render_template('payment.html', cart=cart, error='GCash payment initiation failed.')
        elif payment_method == 'PayMaya':
            payment_response = initiate_paymaya_payment(total, order_id, description)
            if payment_response['status'] == 'success':
                status = 'Processing'
                payment_id = payment_response['payment_id']
            else:
                return render_template('payment.html', cart=cart, error='PayMaya payment initiation failed.')
        else:  # COD
            status = 'Processing'
            payment_id = None

        # Store order details
        order = {
            'order_id': order_id,
            'user_email': session.get('user'),
            'user_name': next((u['name'] for u in users if u['email'] == session.get('user')), 'User'),
            'phone': phone,
            'address': address,
            'postal': postal,
            'city': city,
            'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Use current date and time
            'items': [item['name'] for item in cart],
            'total': total,
            'payment_method': payment_method,
            'payment_id': payment_id,
            'status': status
        }
        all_orders.append(order)
        receipt = {
            'order_id': order_id,
            'items': cart,
            'total': total,
            'payment_method': payment_method,
            'email': email,
            'phone': phone,
            'address': address,
            'postal': postal,
            'city': city,
            'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Use current date and time
            'status': status
        }
        session['receipt'] = receipt
        session['cart'] = []  # Clear cart after payment
        if payment_method in ['GCash', 'PayMaya']:
            return redirect(url_for('payment', order_id=order_id))
        else:
            return redirect(url_for('receipt', order_id=order_id))
    return render_template('payment.html', cart=cart)

@app.route('/receipt')
def receipt():
    if 'user' not in session:
        return redirect(url_for('login'))
    receipt = session.get('receipt')
    if not receipt:
        return redirect(url_for('dashboard'))
    return render_template('receipt.html', receipt=receipt)

# Global variable to store orders (in a real app, this would be a database)
all_orders = []

@app.route('/admin_dashboard')
def admin_dashboard():
    user_email = session.get('user')
    if not user_email:
        return redirect(url_for('login'))
    user = next((u for u in users if u['email'] == user_email), None)
    if not user or user.get('role') != 'admin':
        return redirect(url_for('dashboard'))  # Redirect non-admins to user dashboard
    # Mock aggregated data for admin
    total_users = len(users)
    total_orders = len(all_orders)  # Use actual count
    total_revenue = sum(order['total'] for order in all_orders)
    # Calculate orders per user
    orders_per_user = {}
    for order in all_orders:
        email = order['user_email']
        if email not in orders_per_user:
            orders_per_user[email] = 0
        orders_per_user[email] += 1
    return render_template('admin_dashboard.html', users=users, total_users=total_users, total_orders=total_orders, total_revenue=total_revenue, all_orders=all_orders, orders_per_user=orders_per_user)

@app.route('/api/orders')
def api_orders():
    user_email = session.get('user')
    if not user_email:
        return {'error': 'Not logged in'}, 401
    user = next((u for u in users if u['email'] == user_email), None)
    if not user or user.get('role') != 'admin':
        return {'error': 'Unauthorized'}, 403
    total_revenue = sum(order['total'] for order in all_orders)
    return {'orders': all_orders, 'total_users': len(users), 'total_orders': len(all_orders), 'total_revenue': total_revenue}

@app.route('/api/user_orders')
def api_user_orders():
    user_email = session.get('user')
    if not user_email:
        return {'error': 'Not logged in'}, 401
    # All user orders for notifications
    all_user_orders = [order for order in all_orders if order.get('user_email') == user_email]
    # Dynamic order history for the user (exclude cancelled orders)
    user_orders = [order for order in all_user_orders if order.get('status') != 'Cancelled']
    order_history = [
        {'order_id': order['order_id'], 'date': order['date'], 'items': order['items'], 'status': order['status']}
        for order in user_orders
    ]
    # Dynamic notifications based on all user orders (including cancelled)
    notifications = []
    if all_user_orders:
        recent_order = all_user_orders[-1]  # Most recent order
        if recent_order['status'] == 'Delivered':
            notifications.append('Rate your recent order.')
        elif recent_order['status'] == 'Processing':
            notifications.append('Your order is being processed.')
        elif recent_order['status'] == 'Paid':
            notifications.append('Your order has been confirmed!')
        elif recent_order['status'] == 'Cancelled':
            notifications.append('Your order has been cancelled.')
    else:
        notifications.append('Welcome! Start by browsing our menu.')
    notifications.append('New promotion: 20% off on desserts.')
    return {'order_history': order_history, 'notifications': notifications}

@app.route('/cancel_order/<order_id>', methods=['POST'])
def cancel_order(order_id):
    user_email = session.get('user')
    if not user_email:
        return {'error': 'Not logged in'}, 401
    user = next((u for u in users if u['email'] == user_email), None)
    if not user or user.get('role') != 'admin':
        return {'error': 'Unauthorized'}, 403
    order = next((o for o in all_orders if o['order_id'] == order_id), None)
    if order and order['status'] != 'Cancelled':
        order['status'] = 'Cancelled'
        # Emit real-time updates
        socketio.emit('order_update', {'order_id': order_id, 'status': 'Cancelled', 'user_email': order['user_email']})
        return {'success': True}
    return {'error': 'Invalid order ID or status'}, 400

@app.route('/approve_order/<order_id>', methods=['POST'])
def approve_order(order_id):
    user_email = session.get('user')
    if not user_email:
        return {'error': 'Not logged in'}, 401
    user = next((u for u in users if u['email'] == user_email), None)
    if not user or user.get('role') != 'admin':
        return {'error': 'Unauthorized'}, 403
    order = next((o for o in all_orders if o['order_id'] == order_id), None)
    if order and order['status'] == 'Processing':
        order['status'] = 'Paid'
        # Emit real-time updates
        socketio.emit('order_update', {'order_id': order_id, 'status': 'Paid', 'user_email': order['user_email']})
        return {'success': True}
    return {'error': 'Invalid order ID or status'}, 400

@socketio.on('connect')
def handle_connect():
    user_email = session.get('user')
    if user_email:
        join_room(user_email)
        user = next((u for u in users if u['email'] == user_email), None)
        if user and user.get('role') == 'admin':
            join_room('admin')
        print(f'User {user_email} connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@app.route('/payment_status/<order_id>')
def payment_status(order_id):
    order = next((o for o in all_orders if o.get('order_id') == order_id), None)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    # Mock status update: in production, check with API
    if order['status'] == 'Processing':
        # Simulate payment completion after some time
        import random
        if random.choice([True, False]):  # Randomly mark as paid
            order['status'] = 'Paid'
    return jsonify({'status': order['status']})

if __name__ == '__main__':
    socketio.run(app, debug=True)
