# 🚀 INVOICE MANAGEMENT SYSTEM - BUILD GUIDE
# =====================================================

## PHASE 1: PROJECT SETUP

### Step 1: Create Project Directory
```bash
# Create project folder
mkdir invoice_management_system
cd invoice_management_system

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
# source venv/bin/activate

# Install required packages
pip install Flask==2.0.1
pip install Flask-SQLAlchemy==2.5.1
pip install SQLAlchemy==1.4.23
pip install reportlab==3.6.8
pip install Pillow==8.4.0
pip install python-dateutil==2.8.2
pip install Werkzeug==2.0.1

# Save dependencies
pip freeze > requirements.txt
```

### Step 2: Create Project Structure
```bash
# Create directories
mkdir templates
mkdir static
mkdir static/css
mkdir static/js

# Create main files
touch app.py
touch generate_invoice_pdf.py
touch README.md
```

## PHASE 2: DATABASE MODELS

### Step 3: Create app.py with Database Models
```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib
import json
import os
import tempfile
import re

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mechanic_shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    role = db.Column(db.String(20))
    company_id = db.Column(db.String(50))

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    vehicles = db.relationship('Vehicle', backref='customer', lazy=True)
    invoices = db.relationship('Invoice', backref='customer', lazy=True)

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    year = db.Column(db.Integer)
    make = db.Column(db.String(50))
    model = db.Column(db.String(50))
    vin = db.Column(db.String(17))
    license_plate = db.Column(db.String(20))
    
    invoices = db.relationship('Invoice', backref='vehicle', lazy=True)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'))
    status = db.Column(db.String(20))
    subtotal = db.Column(db.Float)
    tax_rate = db.Column(db.Float, default=13.0)
    tax_amount = db.Column(db.Float)
    total = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = db.relationship('InvoiceItem', backref='invoice', lazy=True)

class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    description = db.Column(db.String(200))
    quantity = db.Column(db.Integer)
    unit_price = db.Column(db.Float)
    total = db.Column(db.Float)

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    city = db.Column(db.String(50))
    postal_code = db.Column(db.String(10))
    phone1 = db.Column(db.String(20))
    phone2 = db.Column(db.String(20))
    services = db.Column(db.Text)

class ServiceTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_type = db.Column(db.String(50), nullable=False)
    service_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Helper Functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_invoice_record(customer_id, vehicle_id, items, notes="", tax_rate=13.0):
    subtotal = sum(item['total'] for item in items)
    tax_amount = subtotal * (tax_rate / 100)
    total = subtotal + tax_amount
    
    invoice = Invoice(
        invoice_number=f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        customer_id=customer_id,
        vehicle_id=vehicle_id,
        status="pending",
        subtotal=subtotal,
        tax_rate=tax_rate,
        tax_amount=tax_amount,
        total=total,
        notes=notes
    )
    db.session.add(invoice)
    db.session.commit()
    
    for item in items:
        invoice_item = InvoiceItem(
            invoice_id=invoice.id,
            description=item['description'],
            quantity=item.get('quantity', 1),
            unit_price=item.get('unit_price', item['total']),
            total=item['total']
        )
        db.session.add(invoice_item)
    
    db.session.commit()
    return invoice

# Initialize app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created!")
    app.run(debug=True, host='0.0.0.0', port=5000)
```

## PHASE 3: AUTHENTICATION SYSTEM

### Step 4: Add Authentication Routes
```python
# Add these routes to app.py

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hash_password(password)
        
        user = User.query.filter_by(username=username).first()
        if user and user.password_hash == hashed_password:
            session['logged_in'] = True
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email', '')
        
        # Validation
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('signup.html')
        
        # Create new user
        user = User(
            username=username,
            password_hash=hash_password(password),
            email=email
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Get statistics
    total_customers = Customer.query.count()
    total_invoices = Invoice.query.count()
    total_revenue = db.session.query(db.func.sum(Invoice.total)).scalar() or 0
    
    return render_template('dashboard.html',
                         total_customers=total_customers,
                         total_invoices=total_invoices,
                         total_revenue=total_revenue)
```

## PHASE 4: BASE TEMPLATE SYSTEM

### Step 5: Create base.html template
```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Invoice Management System{% endblock %}</title>
    
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    
    <style>
        :root {
            --primary-color: #4facfe;
            --secondary-color: #00f2fe;
            --success-color: #28a745;
            --danger-color: #dc3545;
            --warning-color: #ffc107;
            --info-color: #17a2b8;
            --dark-color: #343a40;
            --light-color: #f8f9fa;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .navbar-brand {
            font-weight: 700;
            font-size: 1.5rem;
        }
        
        .main-content {
            padding: 2rem 0;
        }
        
        .card {
            border: none;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .btn {
            border-radius: 10px;
            font-weight: 600;
            padding: 0.75rem 1.5rem;
        }
        
        .alert {
            border-radius: 10px;
            border: none;
        }
    </style>
    
    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('dashboard') }}">
                <i class="fas fa-file-invoice-dollar"></i>
                Invoice Pro
            </a>
            
            {% if session.logged_in %}
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('dashboard') }}">
                            <i class="fas fa-tachometer-alt"></i> Dashboard
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('create_invoice') }}">
                            <i class="fas fa-plus"></i> Create Invoice
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('invoices') }}">
                            <i class="fas fa-list"></i> Invoices
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('customers') }}">
                            <i class="fas fa-users"></i> Customers
                        </a>
                    </li>
                </ul>
                
                <ul class="navbar-nav">
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-bs-toggle="dropdown">
                            <i class="fas fa-user"></i> {{ session.username }}
                        </a>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" href="{{ url_for('logout') }}">
                                <i class="fas fa-sign-out-alt"></i> Logout
                            </a></li>
                        </ul>
                    </li>
                </ul>
            </div>
            {% endif %}
        </div>
    </nav>
    
    <!-- Flash Messages -->
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            <div class="container mt-3">
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            </div>
        {% endif %}
    {% endwith %}
    
    <!-- Main Content -->
    <div class="container main-content">
        {% block content %}{% endblock %}
    </div>
    
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### Step 6: Create Login Template
```html
<!-- templates/login.html -->
{% extends "base.html" %}
{% block title %}Login - Invoice Pro{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6 col-lg-4">
        <div class="card">
            <div class="card-body p-5">
                <div class="text-center mb-4">
                    <i class="fas fa-file-invoice-dollar fa-3x text-primary mb-3"></i>
                    <h2 class="h3 mb-3 font-weight-normal">Sign In</h2>
                    <p class="text-muted">Enter your credentials to access your account</p>
                </div>
                
                <form method="POST">
                    <div class="mb-3">
                        <label for="username" class="form-label">Username</label>
                        <input type="text" class="form-control" id="username" name="username" required>
                    </div>
                    
                    <div class="mb-3">
                        <label for="password" class="form-label">Password</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    
                    <button type="submit" class="btn btn-primary w-100 mb-3">
                        <i class="fas fa-sign-in-alt"></i> Sign In
                    </button>
                </form>
                
                <div class="text-center">
                    <p class="mb-0">Don't have an account? 
                        <a href="{{ url_for('signup') }}" class="text-primary">Sign up</a>
                    </p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

## PHASE 5: CORE BUSINESS ROUTES

### Step 7: Add Customer Management
```python
# Add to app.py

@app.route('/customers')
def customers():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    customers_list = Customer.query.all()
    return render_template('customers.html', customers=customers_list)

@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name'].strip()
        phone = request.form['phone'].strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        
        # Validation
        if not name or not phone:
            flash('Name and phone are required', 'error')
            return render_template('add_customer.html')
        
        customer = Customer(
            name=name,
            phone=phone,
            email=email if email else None,
            address=address if address else None
        )
        
        db.session.add(customer)
        db.session.commit()
        
        flash('Customer added successfully!', 'success')
        return redirect(url_for('customers'))
    
    return render_template('add_customer.html')

@app.route('/create_invoice', methods=['GET', 'POST'])
def create_invoice():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        customer_name = request.form['customer_name'].strip()
        customer_phone = request.form['customer_phone'].strip()
        service_descriptions = request.form.getlist('service_description[]')
        service_amounts = request.form.getlist('service_amount[]')
        tax_rate = float(request.form.get('tax_rate', 13.0))
        
        # Create or find customer
        customer = Customer.query.filter_by(name=customer_name).first()
        if not customer:
            customer = Customer(name=customer_name, phone=customer_phone)
            db.session.add(customer)
            db.session.commit()
        
        # Create invoice items
        items = []
        for i, desc in enumerate(service_descriptions):
            if desc.strip() and i < len(service_amounts):
                amount = float(service_amounts[i])
                items.append({
                    'description': desc.strip(),
                    'total': amount
                })
        
        if not items:
            flash('Please add at least one service item', 'error')
            return render_template('create_invoice.html')
        
        # Create invoice
        invoice = create_invoice_record(
            customer_id=customer.id,
            vehicle_id=None,
            items=items,
            tax_rate=tax_rate
        )
        
        flash('Invoice created successfully!', 'success')
        return redirect(url_for('view_invoice', invoice_id=invoice.id))
    
    return render_template('create_invoice.html')

@app.route('/invoices')
def invoices():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    invoices_list = Invoice.query.order_by(Invoice.created_at.desc()).all()
    return render_template('invoices.html', invoices=invoices_list)

@app.route('/view_invoice/<int:invoice_id>')
def view_invoice(invoice_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template('view_invoice.html', invoice=invoice)
```

## PHASE 6: CONTINUE BUILDING...

This is the foundation! Continue building by adding:
- More templates (dashboard.html, create_invoice.html, etc.)
- PDF generation functionality
- Advanced styling and JavaScript
- Service management features
- Multi-company support

The complete build process involves 8 phases total. This gives you the core foundation to start with! 