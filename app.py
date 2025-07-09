#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib
import json
import os
import time
from generate_invoice_pdf import generate_invoice_pdf
import tempfile
import re

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mechanic_shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Sample data for demo purposes
total_invoices = 25
total_revenue = 12500.00
current_year = datetime.now().year
today = datetime.now().strftime('%Y-%m-%d')

# Sample data for demonstration
sample_invoice = {
    "id": 1,
    "invoice_number": "INV-2024-001",
    "date": datetime(2024, 6, 18),
    "status": "pending",
    "customer": {"name": "John Smith", "phone": "416-555-0123", "email": "john.smith@email.com"},
    "vehicle": {"year": 2022, "make": "Toyota", "model": "Camry", "vin": "1HGBH41JXMN109186", "license_plate": "ABC123"},
    "items": [
        {"description": "Oil Change & Filter", "quantity": 1, "unit_price": 75.00, "total": 75.00},
        {"description": "Brake Inspection", "quantity": 1, "unit_price": 45.00, "total": 45.00},
        {"description": "Engine Oil (5W-30)", "quantity": 1, "unit_price": 25.00, "total": 25.00},
        {"description": "Oil Filter", "quantity": 1, "unit_price": 15.00, "total": 15.00}
    ],
    "subtotal": 160.00,
    "tax_rate": 13,
    "tax_amount": 20.80,
    "total": 180.80,
    "notes": "Regular maintenance service completed. All fluids checked and topped up.",
    "payment_method": "credit",
    "payment_reference": "REF-2024-001"
}

# List to store created invoices
sample_invoices = [sample_invoice]

print('Current working directory:', os.getcwd())
print('app.py is being executed')

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

class CustomPrice(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(100))
    price = db.Column(db.Float)
    company_id = db.Column(db.String(50))
    username = db.Column(db.String(80))

class ServiceTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_type = db.Column(db.String(50), nullable=False)  # 'cn_motors', 'cn_collision', 'generic'
    service_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_customer_by_id(customer_id):
    return Customer.query.get(customer_id)

def get_vehicle_by_id(vehicle_id):
    return Vehicle.query.get(vehicle_id)

def get_invoice_by_id(invoice_id):
    return Invoice.query.get(invoice_id)

def create_invoice_record(customer_id, vehicle_id, items, notes="", tax_rate=13.0):
    # Calculate totals
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

def update_invoice_status(invoice_id, status):
    invoice = get_invoice_by_id(invoice_id)
    if invoice:
        invoice.status = status
        db.session.commit()
        return True
    return False

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        print("=== SIGNUP POST REQUEST RECEIVED ===")
        print(f"Full form data: {dict(request.form)}")
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        terms = request.form.get('terms')
        
        print(f"Parsed data: username='{username}', email='{email}', password_len={len(password)}, confirm_password_len={len(confirm_password)}, terms='{terms}'")

        users = User.query.all()
        # Validate required fields (email is now optional)
        if not username or not password or not confirm_password or not terms:
            error = 'Username, password, and terms agreement are required.'
            flash(error, 'danger')
            print(f"Validation error: {error}")
            return render_template('signup.html', error=error)
        if len(username) < 3:
            error = 'Username must be at least 3 characters.'
            flash(error, 'danger')
            return render_template('signup.html', error=error)
        if len(password) < 6:
            error = 'Password must be at least 6 characters.'
            flash(error, 'danger')
            return render_template('signup.html', error=error)
        if password != confirm_password:
            error = 'Passwords do not match.'
            flash(error, 'danger')
            return render_template('signup.html', error=error)
        if User.query.filter_by(username=username).first():
            error = 'Username already exists.'
            flash(error, 'danger')
            return render_template('signup.html', error=error)
        
        # Only check email uniqueness if email is provided
        if email:
            for u in users:
                if u.email and u.email == email:
                    error = 'Email already registered.'
                    flash(error, 'danger')
                    return render_template('signup.html', error=error)
        
        # Save new user (email can be empty)
        user = User(
            username=username,
            password_hash=hash_password(password),
            email=email if email else ''
        )
        db.session.add(user)
        db.session.commit()
        print(f"User {username} created successfully")  # Debug print
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        print("=== LOGIN POST REQUEST RECEIVED ===")
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        print(f"Login attempt - Username: '{username}', Password provided: {bool(password)}")
        
        users = User.query.all()
        print(f"Total users in database: {len(users)}")
        for user in users:
            print(f"User: {user.username}, Hash: {user.password_hash[:20]}...")
        
        if not username or not password:
            error = 'Username and password are required.'
            print(f"Login error: {error}")
            return render_template('login.html', error=error)
        
        hashed_input_password = hash_password(password)
        print(f"Hashed input password: {hashed_input_password[:20]}...")
        
        for user in users:
            if user.username == username and user.password_hash == hashed_input_password:
                print("Login successful!")
                session['logged_in'] = True
                session['username'] = username
                session['user_email'] = user.email
                return redirect(url_for('dashboard'))
        else:
            error = 'Invalid username or password.'
            print(f"Login failed: {error}")
            return render_template('login.html', error=error)
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    company = Company.query.first()
    if company:
        print(f"Dashboard: Company name fetched: {company.name}") # Debug print
    else:
        print("Dashboard: No company found in DB.") # Debug print
    
    # Calculate real statistics from database
    total_invoices_count = Invoice.query.count()
    total_revenue_amount = db.session.query(db.func.sum(Invoice.total)).scalar() or 0.0
    total_customers_count = Customer.query.count()
    total_vehicles_count = Vehicle.query.count()
    current_year = datetime.now().year
    today = datetime.now().strftime('%B %d, %Y')
    
    # Get selected company from session (if any)
    selected_company = session.get('selected_company', 'generic')
    
    return render_template('dashboard.html', 
                         company=company, 
                         total_invoices_count=total_invoices_count, 
                         total_revenue=total_revenue_amount, 
                         total_customers_count=total_customers_count,
                         total_vehicles_count=total_vehicles_count,
                         current_year=current_year, 
                         current_date=today, 
                         session=session,
                         selected_company=selected_company)

@app.route('/view_invoice/<int:invoice_id>')
def view_invoice(invoice_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    company = Company.query.first()
    if company:
        print(f"View Invoice: Company name fetched: {company.name}") # Debug print
    else:
        print("View Invoice: No company found in DB.") # Debug print
    invoice_data = get_invoice_by_id(invoice_id)
    if not invoice_data:
        flash("Invoice not found!", "error")
        return redirect(url_for("invoices"))
    
    # Get selected company from session for proper branding
    selected_company = session.get('selected_company', 'generic')
    
    return render_template("view_invoice.html", 
                         invoice=invoice_data, 
                         company=company, 
                         session=session,
                         selected_company=selected_company)

@app.route('/download_invoice_pdf/<int:invoice_id>')
def download_invoice_pdf(invoice_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Get invoice and company data
    invoice = get_invoice_by_id(invoice_id)
    company = Company.query.first()
    
    if not invoice or not company:
        flash("Invoice or company data not found!", "error")
        return redirect(url_for("invoices"))
    
    # Determine proper company name based on selected company type
    selected_company = session.get('selected_company', 'generic')
    company_names = {
        'cn_motors': 'CN Motors Ltd',
        'cn_collision': 'CN Auto Collision',
        'generic': 'Universal Invoice System'
    }
    
    # Use the proper company name or fall back to database company name
    final_company_name = company_names.get(selected_company, company.name)
    
    # Prepare data for PDF generation
    pdf_data = {
        'title': 'RECEIPT',
        'company': {
            'name': final_company_name,
            'address_lines': [
                company.address or "1770 Albion Rd, unit 53",
                f"{company.city or 'Etobicoke'}, ON {company.postal_code or 'M9V 4J9'}"
            ],
            'phones': [phone for phone in [company.phone1, company.phone2] if phone]
        },
        'customer': {
            'name': invoice.customer.name
        },
        'receipt_number': invoice.id,
        'items': [
            {
                'description': item.description,
                'amount': item.total
            }
            for item in invoice.items
        ],
        'subtotal': invoice.subtotal or 0.0,
        'hst_rate': invoice.tax_rate or 13.0,
        'hst_amount': invoice.tax_amount or 0.0,
        'total': invoice.total or 0.0
    }
    
    # Generate PDF in a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        generate_invoice_pdf(tmp_file.name, pdf_data)
        
        # Send the file
        return send_file(
            tmp_file.name,
            as_attachment=True,
            download_name=f"invoice_{invoice.invoice_number}.pdf",
            mimetype='application/pdf'
        )

@app.route('/create_invoice', methods=['GET', 'POST'])
def create_invoice():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    company = Company.query.first()
    
    if request.method == 'POST':
        print("=== CREATE INVOICE POST REQUEST RECEIVED ===")
        print(f"Form data: {dict(request.form)}")
        
        # Get customer information
        customer_name = request.form.get('customer_name', '').strip()
        customer_phone = request.form.get('customer_phone', '').strip()
        
        # Get service information
        service_descriptions = request.form.getlist('service_description[]')
        service_amounts = request.form.getlist('service_amount[]')
        
        # Get calculated totals and tax rate
        subtotal = request.form.get('subtotal', '0')
        tax_rate = request.form.get('tax_rate', '13.0')
        tax_amount = request.form.get('tax_amount', '0')
        total = request.form.get('total', '0')
        
        print(f"Customer: name='{customer_name}', phone='{customer_phone}'")
        print(f"Services: descriptions={service_descriptions}, amounts={service_amounts}")
        print(f"Totals: subtotal={subtotal}, tax_rate={tax_rate}, tax_amount={tax_amount}, total={total}")
        
        # Validate customer information
        if not customer_name:
            print("Error: No customer name provided")
            flash('Customer name is required.', 'error')
            selected_company = session.get('selected_company', 'generic')
            predefined_services = ServiceTemplate.query.filter_by(company_type=selected_company, is_active=True).all()
            company_names = {'cn_motors': 'CN Motors Ltd', 'cn_collision': 'CN Auto Collision', 'generic': 'Universal Invoice System'}
            company_name = company_names.get(selected_company, 'Invoice System')
            return render_template('create_invoice.html', company=company, predefined_services=predefined_services, selected_company=selected_company, company_name=company_name)
        
        if len(customer_name) < 2 or len(customer_name) > 100:
            print("Error: Invalid customer name length")
            flash('Customer name must be between 2 and 100 characters.', 'error')
            selected_company = session.get('selected_company', 'generic')
            predefined_services = ServiceTemplate.query.filter_by(company_type=selected_company, is_active=True).all()
            company_names = {'cn_motors': 'CN Motors Ltd', 'cn_collision': 'CN Auto Collision', 'generic': 'Universal Invoice System'}
            company_name = company_names.get(selected_company, 'Invoice System')
            return render_template('create_invoice.html', company=company, predefined_services=predefined_services, selected_company=selected_company, company_name=company_name)
        
        if not re.match(r'^[a-zA-Z\s\-\'.]+$', customer_name):
            print("Error: Invalid customer name format")
            flash('Customer name should only contain letters, spaces, hyphens, and apostrophes.', 'error')
            selected_company = session.get('selected_company', 'generic')
            predefined_services = ServiceTemplate.query.filter_by(company_type=selected_company, is_active=True).all()
            company_names = {'cn_motors': 'CN Motors Ltd', 'cn_collision': 'CN Auto Collision', 'generic': 'Universal Invoice System'}
            company_name = company_names.get(selected_company, 'Invoice System')
            return render_template('create_invoice.html', company=company, predefined_services=predefined_services, selected_company=selected_company, company_name=company_name)
        
        if not customer_phone:
            print("Error: No customer phone provided")
            flash('Customer phone number is required.', 'error')
            selected_company = session.get('selected_company', 'generic')
            predefined_services = ServiceTemplate.query.filter_by(company_type=selected_company, is_active=True).all()
            company_names = {'cn_motors': 'CN Motors Ltd', 'cn_collision': 'CN Auto Collision', 'generic': 'Universal Invoice System'}
            company_name = company_names.get(selected_company, 'Invoice System')
            return render_template('create_invoice.html', company=company, predefined_services=predefined_services, selected_company=selected_company, company_name=company_name)
        
        if not re.match(r'^\(\d{3}\) \d{3}-\d{4}$', customer_phone):
            print("Error: Invalid phone number format")
            flash('Phone number must be in format (123) 456-7890.', 'error')
            selected_company = session.get('selected_company', 'generic')
            predefined_services = ServiceTemplate.query.filter_by(company_type=selected_company, is_active=True).all()
            company_names = {'cn_motors': 'CN Motors Ltd', 'cn_collision': 'CN Auto Collision', 'generic': 'Universal Invoice System'}
            company_name = company_names.get(selected_company, 'Invoice System')
            return render_template('create_invoice.html', company=company, predefined_services=predefined_services, selected_company=selected_company, company_name=company_name)
        
        # Convert to floats with error handling
        try:
            subtotal = float(subtotal) if subtotal else 0
            tax_rate = float(tax_rate) if tax_rate else 13.0
            tax_amount = float(tax_amount) if tax_amount else 0
            total = float(total) if total else 0
        except ValueError as e:
            print(f"Error converting values to float: {e}")
            flash('Invalid numerical values in form.', 'error')
            selected_company = session.get('selected_company', 'generic')
            predefined_services = ServiceTemplate.query.filter_by(company_type=selected_company, is_active=True).all()
            company_names = {'cn_motors': 'CN Motors Ltd', 'cn_collision': 'CN Auto Collision', 'generic': 'Universal Invoice System'}
            company_name = company_names.get(selected_company, 'Invoice System')
            return render_template('create_invoice.html', company=company, predefined_services=predefined_services, selected_company=selected_company, company_name=company_name)
        
        print(f"Converted values - subtotal={subtotal}, tax_rate={tax_rate}, total={total}")
            
        if not service_descriptions or not service_descriptions[0].strip():
            print("Error: No service descriptions provided")
            flash('At least one service description is required.', 'error')
            selected_company = session.get('selected_company', 'generic')
            predefined_services = ServiceTemplate.query.filter_by(company_type=selected_company, is_active=True).all()
            company_names = {'cn_motors': 'CN Motors Ltd', 'cn_collision': 'CN Auto Collision', 'generic': 'Universal Invoice System'}
            company_name = company_names.get(selected_company, 'Invoice System')
            return render_template('create_invoice.html', company=company, predefined_services=predefined_services, selected_company=selected_company, company_name=company_name)
        
        try:
            print("Creating or finding customer...")
            # Create or find customer
            customer = Customer.query.filter_by(name=customer_name).first()
            if not customer:
                print(f"Creating new customer: {customer_name}")
                customer = Customer(
                    name=customer_name,
                    phone=customer_phone,
                    email='',
                    address='',
                    created_at=datetime.now()
                )
                db.session.add(customer)
                db.session.commit()
                print(f"Customer created with ID: {customer.id}")
            else:
                print(f"Found existing customer with ID: {customer.id}")
            
            # Create invoice items
            print("Processing invoice items...")
            items = []
            for i, desc in enumerate(service_descriptions):
                if desc.strip() and i < len(service_amounts):
                    try:
                        amount = float(service_amounts[i])
                        print(f"Adding item: {desc.strip()} - ${amount}")
                        items.append({
                            'description': desc.strip(),
                            'quantity': 1,
                            'unit_price': amount,
                            'total': amount
                        })
                    except ValueError as e:
                        print(f"Error converting amount to float: {e}")
                        continue
            
            if not items:
                print("Error: No valid items created")
                flash('Please add at least one valid service item.', 'error')
                selected_company = session.get('selected_company', 'generic')
                predefined_services = ServiceTemplate.query.filter_by(company_type=selected_company, is_active=True).all()
                company_names = {'cn_motors': 'CN Motors Ltd', 'cn_collision': 'CN Auto Collision', 'generic': 'Universal Invoice System'}
                company_name = company_names.get(selected_company, 'Invoice System')
                return render_template('create_invoice.html', company=company, predefined_services=predefined_services, selected_company=selected_company, company_name=company_name)
            
            print(f"Created {len(items)} invoice items")
            
            # Create the invoice with the correct tax rate
            print("Creating invoice record...")
            invoice = create_invoice_record(
                customer_id=customer.id,
                vehicle_id=None,
                items=items,
                notes='',
                tax_rate=tax_rate
            )
            
            print(f"Invoice created successfully! ID: {invoice.id}")
            flash('Receipt created successfully!', 'success')
            return redirect(url_for('view_invoice', invoice_id=invoice.id))
            
        except Exception as e:
            print(f"Error creating invoice: {e}")
            import traceback
            traceback.print_exc()
            flash(f'Error creating receipt: {str(e)}', 'error')
            db.session.rollback()
            selected_company = session.get('selected_company', 'generic')
            predefined_services = ServiceTemplate.query.filter_by(company_type=selected_company, is_active=True).all()
            company_names = {'cn_motors': 'CN Motors Ltd', 'cn_collision': 'CN Auto Collision', 'generic': 'Universal Invoice System'}
            company_name = company_names.get(selected_company, 'Invoice System')
            return render_template('create_invoice.html', company=company, predefined_services=predefined_services, selected_company=selected_company, company_name=company_name)
    
    print("GET request - showing create invoice form")
    
    # Get the selected company type from session
    selected_company = session.get('selected_company', 'generic')
    
    # Get predefined services for the selected company type
    predefined_services = ServiceTemplate.query.filter_by(
        company_type=selected_company, 
        is_active=True
    ).all()
    
    # Set company name based on selected company type
    company_names = {
        'cn_motors': 'CN Motors Ltd',
        'cn_collision': 'CN Auto Collision',
        'generic': 'Universal Invoice System'
    }
    company_name = company_names.get(selected_company, 'Invoice System')
    
    return render_template('create_invoice.html', 
                         company=company,
                         predefined_services=predefined_services,
                         selected_company=selected_company,
                         company_name=company_name)

@app.route('/invoices')
def invoices():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    invoices = Invoice.query.all()
    company_id = session.get('company_id', 'generic')
    current_company = Company.query.get(company_id)
    return render_template('invoices.html', invoices=invoices, company=current_company)

@app.route('/revenue_login', methods=['GET', 'POST'])
def revenue_login():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    company_id = session.get('company_id', 'generic')
    current_company = Company.query.get(company_id)
    if request.method == 'POST':
        session['revenue_authorized'] = True
        flash("Revenue access granted.")
        return redirect(url_for("dashboard"))
    return render_template("revenue_login.html", company=current_company)

@app.route('/revenue')
def view_revenue():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    if not session.get('revenue_authorized'):
         flash("Please log in to view revenue.")
         return redirect(url_for("revenue_login"))
    company_id = session.get('company_id', 'generic')
    current_company = Company.query.get(company_id)
    return render_template("revenue.html", total_revenue=total_revenue, company=current_company)

@app.route('/select_company')
def select_company():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    try:
        companies = Company.query.all()
        if not companies:
            # Create default company if none exist
            default_company = Company(name="Cn Auto Collision Inc.")
            db.session.add(default_company)
            db.session.commit()
            companies = [default_company]
        
        return render_template("select_company.html", companies=companies)
    except Exception as e:
        print(f"Error in select_company route: {e}")
        flash(f"Error loading companies: {str(e)}", 'error')
        return redirect(url_for('dashboard'))

@app.route('/edit_invoice/<int:invoice_id>', methods=['GET', 'POST'])
def edit_invoice(invoice_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    # In a real app, fetch invoice data (e.g. from a database) and process form data on POST.
    # For demo, we simply flash a message and redirect.
    if request.method == 'POST':
         flash("Invoice updated successfully.")
         return redirect(url_for("dashboard"))
    # For GET, render the edit_invoice template (using dummy invoice data).
    return render_template("edit_invoice.html", invoice=sample_invoice, current_year=current_year)

@app.route('/customers')
def customers():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    company = Company.query.first()
    customers_list = Customer.query.all()
    return render_template('customers.html', customers=customers_list, company=company)

@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer_route():
    message = None
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        
        # Validation
        if not name or not phone:
            message = 'Name and phone are required.'
        elif len(name) < 2 or len(name) > 100:
            message = 'Name must be between 2 and 100 characters.'
        elif not re.match(r'^[a-zA-Z\s\-\'.]+$', name):
            message = 'Name should only contain letters, spaces, hyphens, and apostrophes.'
        elif not re.match(r'^\(\d{3}\) \d{3}-\d{4}$', phone):
            message = 'Phone number must be in format (123) 456-7890.'
        elif email and not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            message = 'Please enter a valid email address.'
        elif email and len(email) > 120:
            message = 'Email address is too long (max 120 characters).'
        elif address and len(address) > 200:
            message = 'Address is too long (max 200 characters).'
        else:
            try:
                # Check if customer with same phone already exists
                existing = Customer.query.filter_by(phone=phone).first()
                if existing:
                    message = f'Customer with phone number {phone} already exists.'
                else:
                    customer = Customer(
                        name=name,
                        phone=phone,
                        email=email if email else None,
                        address=address if address else None
                    )
                    db.session.add(customer)
                    db.session.commit()
                    message = f'Customer "{name}" added successfully! (ID: {customer.id})'
            except Exception as e:
                message = f'Error adding customer: {str(e)}'
                db.session.rollback()
    return render_template('add_customer.html', message=message)

@app.route('/vehicles')
def vehicles():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    company = Company.query.first()
    vehicles_list = Vehicle.query.all()
    return render_template('vehicles.html', vehicles=vehicles_list, company=company)

@app.route('/add_vehicle', methods=['GET', 'POST'])
def add_vehicle_route():
    message = None
    customers_list = Customer.query.all()  # Get all customers for the dropdown
    
    if request.method == 'POST':
        year = request.form.get('year', '').strip()
        make = request.form.get('make', '').strip()
        model = request.form.get('model', '').strip()
        vin = request.form.get('vin', '').strip().upper()
        license_plate = request.form.get('license_plate', '').strip().upper()
        customer_id = request.form.get('customer_id', '').strip()
        
        # Validation
        if not year or not make or not model:
            message = 'Year, make, and model are required.'
        else:
            try:
                year_int = int(year)
                current_year = datetime.now().year
                
                # Validate year range
                if year_int < 1900 or year_int > current_year + 1:
                    message = f'Year must be between 1900 and {current_year + 1}.'
                elif len(make) < 1 or len(make) > 50:
                    message = 'Make must be between 1 and 50 characters.'
                elif not re.match(r'^[a-zA-Z0-9\s\-]+$', make):
                    message = 'Make should only contain letters, numbers, spaces, and hyphens.'
                elif len(model) < 1 or len(model) > 50:
                    message = 'Model must be between 1 and 50 characters.'
                elif not re.match(r'^[a-zA-Z0-9\s\-]+$', model):
                    message = 'Model should only contain letters, numbers, spaces, and hyphens.'
                elif vin and (len(vin) != 17 or not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', vin)):
                    message = 'VIN must be exactly 17 characters with valid format (no I, O, Q).'
                elif license_plate and len(license_plate) > 20:
                    message = 'License plate must be 20 characters or less.'
                else:
                    # Check if VIN already exists
                    if vin:
                        existing_vin = Vehicle.query.filter_by(vin=vin).first()
                        if existing_vin:
                            message = f'Vehicle with VIN {vin} already exists.'
                        else:
                            vehicle = Vehicle(
                                year=year_int,
                                make=make,
                                model=model,
                                vin=vin if vin else None,
                                license_plate=license_plate if license_plate else None,
                                customer_id=int(customer_id) if customer_id else None
                            )
                            db.session.add(vehicle)
                            db.session.commit()
                            message = f'Vehicle "{year_int} {make} {model}" added successfully! (ID: {vehicle.id})'
                    else:
                        vehicle = Vehicle(
                            year=year_int,
                            make=make,
                            model=model,
                            vin=None,
                            license_plate=license_plate if license_plate else None,
                            customer_id=int(customer_id) if customer_id else None
                        )
                        db.session.add(vehicle)
                        db.session.commit()
                        message = f'Vehicle "{year_int} {make} {model}" added successfully! (ID: {vehicle.id})'
                        
            except ValueError as e:
                message = 'Invalid year format. Please enter a valid year.'
            except Exception as e:
                message = f'Error adding vehicle: {str(e)}'
                db.session.rollback()
    
    return render_template('add_vehicle.html', message=message, customers=customers_list)

@app.route('/delete_customer/<int:customer_id>', methods=['POST'])
def delete_customer(customer_id):
    if not session.get('logged_in'):
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Check if customer has any invoices
        if customer.invoices:
            return jsonify({'error': 'Cannot delete customer with existing invoices'}), 400
        
        # Delete associated vehicles first
        for vehicle in customer.vehicles:
            db.session.delete(vehicle)
        
        # Delete the customer
        db.session.delete(customer)
        db.session.commit()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"Error deleting customer: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/delete_vehicle/<int:vehicle_id>', methods=['POST'])
def delete_vehicle(vehicle_id):
    if not session.get('logged_in'):
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        # Check if vehicle has any invoices
        if vehicle.invoices:
            return jsonify({'error': 'Cannot delete vehicle with existing invoices'}), 400
        
        # Delete the vehicle
        db.session.delete(vehicle)
        db.session.commit()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"Error deleting vehicle: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/set_company/<company_type>')
def set_company(company_type):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    session['selected_company'] = company_type
    
    # Redirect to create invoice with company-specific services
    if company_type == 'cn_motors':
        return redirect(url_for('cn_motors_repairs'))
    elif company_type == 'cn_collision':
        return redirect(url_for('cn_collision_repairs'))
    else:
        return redirect(url_for('create_invoice'))

@app.route('/cn_motors_repairs')
def cn_motors_repairs():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    session['selected_company'] = 'cn_motors'
    company = Company.query.first()
    
    # Get services from database grouped by category
    all_services = ServiceTemplate.query.filter_by(company_type='cn_motors', is_active=True).all()
    
    # Group services by category for the template
    services_by_category = {
        'engine': [],
        'brakes': [],
        'suspension': [],
        'electrical': [],
        'cooling': [],
        'parts': []
    }
    
    # Categorize services based on name keywords
    for service in all_services:
        name_lower = service.service_name.lower()
        categorized = False
        
        if any(keyword in name_lower for keyword in ['engine', 'motor', 'oil', 'tune', 'spark']):
            services_by_category['engine'].append({
                'name': service.service_name,
                'price': service.price,
                'description': f'Professional {service.service_name.lower()} service'
            })
            categorized = True
        elif any(keyword in name_lower for keyword in ['brake', 'pad', 'rotor', 'disc']):
            services_by_category['brakes'].append({
                'name': service.service_name,
                'price': service.price,
                'description': f'Quality {service.service_name.lower()} service'
            })
            categorized = True
        elif any(keyword in name_lower for keyword in ['suspension', 'shock', 'strut', 'spring']):
            services_by_category['suspension'].append({
                'name': service.service_name,
                'price': service.price,
                'description': f'Expert {service.service_name.lower()} service'
            })
            categorized = True
        elif any(keyword in name_lower for keyword in ['electrical', 'battery', 'alternator', 'starter']):
            services_by_category['electrical'].append({
                'name': service.service_name,
                'price': service.price,
                'description': f'Professional {service.service_name.lower()} service'
            })
            categorized = True
        elif any(keyword in name_lower for keyword in ['cooling', 'radiator', 'coolant', 'thermostat']):
            services_by_category['cooling'].append({
                'name': service.service_name,
                'price': service.price,
                'description': f'Expert {service.service_name.lower()} service'
            })
            categorized = True
        
        # If not categorized, add to parts
        if not categorized:
            services_by_category['parts'].append({
                'name': service.service_name,
                'price': service.price,
                'description': f'Quality {service.service_name.lower()}'
            })
    
    # Create repair_options structure for template compatibility
    class RepairOptions:
        def __init__(self, categories):
            for key, value in categories.items():
                setattr(self, key, value)
    
    company.repair_options = RepairOptions(services_by_category)
    
    return render_template('cn_motors_repairs.html', 
                         company=company,
                         company_name="CN Motors Ltd",
                         selected_company='cn_motors')

@app.route('/cn_collision_repairs')
def cn_collision_repairs():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    session['selected_company'] = 'cn_collision'
    company = Company.query.first()
    
    # Get services from database grouped by category
    all_services = ServiceTemplate.query.filter_by(company_type='cn_collision', is_active=True).all()
    
    # Group services by category for the template
    services_by_category = {
        'front_end': [],
        'rear_end': [],
        'side_panels': [],
        'glass': [],
        'paint_services': [],
        'frame': []
    }
    
    # Categorize services based on name keywords
    for service in all_services:
        name_lower = service.service_name.lower()
        categorized = False
        
        if any(keyword in name_lower for keyword in ['front', 'bumper front', 'headlight', 'grille']):
            services_by_category['front_end'].append({
                'name': service.service_name,
                'price': service.price,
                'description': f'Professional {service.service_name.lower()} repair and replacement'
            })
            categorized = True
        elif any(keyword in name_lower for keyword in ['rear', 'bumper rear', 'taillight', 'trunk']):
            services_by_category['rear_end'].append({
                'name': service.service_name,
                'price': service.price,
                'description': f'Expert {service.service_name.lower()} repair and replacement'
            })
            categorized = True
        elif any(keyword in name_lower for keyword in ['door', 'side', 'panel', 'quarter']):
            services_by_category['side_panels'].append({
                'name': service.service_name,
                'price': service.price,
                'description': f'Quality {service.service_name.lower()} repair and replacement'
            })
            categorized = True
        elif any(keyword in name_lower for keyword in ['glass', 'window', 'windshield', 'mirror']):
            services_by_category['glass'].append({
                'name': service.service_name,
                'price': service.price,
                'description': f'Professional {service.service_name.lower()} replacement'
            })
            categorized = True
        elif any(keyword in name_lower for keyword in ['paint', 'color', 'refinish', 'clear coat']):
            services_by_category['paint_services'].append({
                'name': service.service_name,
                'price': service.price,
                'description': f'Expert {service.service_name.lower()} with color matching'
            })
            categorized = True
        elif any(keyword in name_lower for keyword in ['frame', 'structural', 'unibody', 'alignment']):
            services_by_category['frame'].append({
                'name': service.service_name,
                'price': service.price,
                'description': f'Professional {service.service_name.lower()} service'
            })
            categorized = True
        
        # If not categorized, add to front_end as default
        if not categorized:
            services_by_category['front_end'].append({
                'name': service.service_name,
                'price': service.price,
                'description': f'Quality {service.service_name.lower()} service'
            })
    
    # Create repair_options structure for template compatibility
    class RepairOptions:
        def __init__(self, categories):
            for key, value in categories.items():
                setattr(self, key, value)
    
    company.repair_options = RepairOptions(services_by_category)
    
    return render_template('cn_collision_repairs.html', 
                         company=company,
                         company_name="CN Auto Collision",
                         selected_company='cn_collision')

@app.route('/generic_services')
def generic_services():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    session['selected_company'] = 'generic'
    company = Company.query.first()
    
    # Get generic services from database
    all_services = ServiceTemplate.query.filter_by(company_type='generic', is_active=True).all()
    
    # Group services by category for the template
    services_by_category = {
        'general': [],
        'consultation': [],
        'custom': [],
        'maintenance': []
    }
    
    # Categorize services based on name keywords
    for service in all_services:
        name_lower = service.service_name.lower()
        categorized = False
        
        if any(keyword in name_lower for keyword in ['consult', 'advice', 'planning', 'assessment']):
            services_by_category['consultation'].append({
                'name': service.service_name,
                'price': service.price,
                'description': f'Professional {service.service_name.lower()} service'
            })
            categorized = True
        elif any(keyword in name_lower for keyword in ['custom', 'special', 'unique', 'bespoke']):
            services_by_category['custom'].append({
                'name': service.service_name,
                'price': service.price,
                'description': f'Customized {service.service_name.lower()} solution'
            })
            categorized = True
        elif any(keyword in name_lower for keyword in ['maintenance', 'cleaning', 'inspection', 'check']):
            services_by_category['maintenance'].append({
                'name': service.service_name,
                'price': service.price,
                'description': f'Regular {service.service_name.lower()} service'
            })
            categorized = True
        
        # If not categorized, add to general as default
        if not categorized:
            services_by_category['general'].append({
                'name': service.service_name,
                'price': service.price,
                'description': f'Quality {service.service_name.lower()} service'
            })
    
    # Create service_options structure for template compatibility
    class ServiceOptions:
        def __init__(self, categories):
            for key, value in categories.items():
                setattr(self, key, value)
    
    company.service_options = ServiceOptions(services_by_category)
    
    return render_template('generic_services.html', 
                         company=company,
                         company_name="Generic Services",
                         selected_company='generic')

@app.route('/save_custom_price', methods=['POST'])
def save_custom_price():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    data = request.get_json()
    service_name = data.get('service_name')
    price = data.get('price')
    company_id = session.get('company_id', 'generic')
    username = session.get('username')
    
    if not service_name or price is None:
        return jsonify({'success': False, 'error': 'Missing service name or price'})
    
    try:
        price = float(price)
        # Save custom price to database
        custom_price = CustomPrice(
            service_name=service_name,
            price=price,
            company_id=company_id,
            username=username
        )
        db.session.add(custom_price)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Price saved successfully'})
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid price format'})

@app.route('/get_custom_prices', methods=['GET'])
def get_custom_prices():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    company_id = session.get('company_id', 'generic')
    username = session.get('username')
    custom_prices = CustomPrice.query.filter_by(company_id=company_id, username=username).all()
    
    return jsonify({'success': True, 'prices': [{'service_name': cp.service_name, 'price': cp.price} for cp in custom_prices]})

@app.route('/manage_services/<company_type>')
def manage_services(company_type):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if company_type not in ['cn_motors', 'cn_collision', 'generic']:
        flash('Invalid company type', 'error')
        return redirect(url_for('dashboard'))
    
    services = ServiceTemplate.query.filter_by(company_type=company_type).order_by(ServiceTemplate.service_name).all()
    
    company_names = {
        'cn_motors': 'CN Motors Ltd',
        'cn_collision': 'CN Auto Collision',
        'generic': 'Generic Invoice System'
    }
    
    return render_template('manage_services.html', 
                         services=services, 
                         company_type=company_type,
                         company_name=company_names.get(company_type, 'Unknown'))

@app.route('/add_service/<company_type>', methods=['POST'])
def add_service(company_type):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    if company_type not in ['cn_motors', 'cn_collision', 'generic']:
        return jsonify({'success': False, 'error': 'Invalid company type'})
    
    data = request.get_json()
    service_name = data.get('service_name', '').strip()
    price = data.get('price')
    
    if not service_name or price is None:
        return jsonify({'success': False, 'error': 'Service name and price are required'})
    
    try:
        price = float(price)
        if price < 0:
            return jsonify({'success': False, 'error': 'Price must be positive'})
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid price format'})
    
    # Check if service already exists
    existing = ServiceTemplate.query.filter_by(company_type=company_type, service_name=service_name).first()
    if existing:
        return jsonify({'success': False, 'error': 'Service already exists'})
    
    try:
        service = ServiceTemplate(
            company_type=company_type,
            service_name=service_name,
            price=price
        )
        db.session.add(service)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Service added successfully',
            'service': {
                'id': service.id,
                'name': service.service_name,
                'price': service.price,
                'is_active': service.is_active
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Error adding service: {str(e)}'})

@app.route('/update_service/<int:service_id>', methods=['POST'])
def update_service(service_id):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    service = ServiceTemplate.query.get(service_id)
    if not service:
        return jsonify({'success': False, 'error': 'Service not found'})
    
    data = request.get_json()
    service_name = data.get('service_name', '').strip()
    price = data.get('price')
    is_active = data.get('is_active', True)
    
    if not service_name or price is None:
        return jsonify({'success': False, 'error': 'Service name and price are required'})
    
    try:
        price = float(price)
        if price < 0:
            return jsonify({'success': False, 'error': 'Price must be positive'})
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid price format'})
    
    # Check if service name already exists (excluding current service)
    existing = ServiceTemplate.query.filter(
        ServiceTemplate.company_type == service.company_type,
        ServiceTemplate.service_name == service_name,
        ServiceTemplate.id != service_id
    ).first()
    if existing:
        return jsonify({'success': False, 'error': 'Service name already exists'})
    
    try:
        service.service_name = service_name
        service.price = price
        service.is_active = bool(is_active)
        service.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Service updated successfully',
            'service': {
                'id': service.id,
                'name': service.service_name,
                'price': service.price,
                'is_active': service.is_active
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Error updating service: {str(e)}'})

@app.route('/delete_service/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    service = ServiceTemplate.query.get(service_id)
    if not service:
        return jsonify({'success': False, 'error': 'Service not found'})
    
    try:
        db.session.delete(service)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Service deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Error deleting service: {str(e)}'})

def initialize_default_services():
    """Initialize default services if they don't exist"""
    if ServiceTemplate.query.count() == 0:
        # CN Motors default services
        cn_motors_services = [
            {"name": "Oil Change", "price": 59.99},
            {"name": "Brake Service", "price": 149.99},
            {"name": "Tire Replacement", "price": 299.99},
            {"name": "Engine Diagnostic", "price": 89.99},
            {"name": "Transmission Service", "price": 199.99},
            {"name": "Air Filter Replacement", "price": 29.99},
            {"name": "Coolant Flush", "price": 79.99},
            {"name": "Battery Test & Replace", "price": 129.99}
        ]
        
        for service in cn_motors_services:
            template = ServiceTemplate(
                company_type='cn_motors',
                service_name=service['name'],
                price=service['price']
            )
            db.session.add(template)
        
        # CN Collision default services
        cn_collision_services = [
            {"name": "Dent Repair", "price": 199.99},
            {"name": "Paint Touch-up", "price": 149.99},
            {"name": "Bumper Replacement", "price": 499.99},
            {"name": "Window Replacement", "price": 299.99},
            {"name": "Full Body Work", "price": 1299.99},
            {"name": "Scratch Removal", "price": 99.99},
            {"name": "Panel Replacement", "price": 699.99},
            {"name": "Frame Straightening", "price": 899.99}
        ]
        
        for service in cn_collision_services:
            template = ServiceTemplate(
                company_type='cn_collision',
                service_name=service['name'],
                price=service['price']
            )
            db.session.add(template)
        
        # Generic default services
        generic_services = [
            {"name": "General Service", "price": 99.99},
            {"name": "Consultation", "price": 149.99},
            {"name": "Custom Work", "price": 199.99},
            {"name": "Maintenance Check", "price": 79.99},
            {"name": "Assessment Report", "price": 125.00},
            {"name": "Planning Service", "price": 175.00},
            {"name": "Custom Solution", "price": 249.99},
            {"name": "Regular Maintenance", "price": 89.99}
        ]
        
        for service in generic_services:
            template = ServiceTemplate(
                company_type='generic',
                service_name=service['name'],
                price=service['price']
            )
            db.session.add(template)
        
        db.session.commit()
        print("Default services initialized")

@app.route('/company_settings', methods=['GET', 'POST'])
def company_settings():
    company = Company.query.first()
    if not company:
        company = Company(name="Cn Auto Collision Inc.")
        db.session.add(company)
        db.session.commit()
    
    if request.method == 'POST':
        print("Company settings POST request received") # Debug print
        new_name = request.form.get('company_name', '').strip()
        print(f"Received company name: '{new_name}'") # Debug print
        
        if new_name:
            try:
                company.name = new_name
                db.session.commit()
                print(f"Company name updated to: {company.name}") # Debug print
                flash("Company name updated successfully!", 'success')
                # Redirect to avoid form resubmission
                return redirect(url_for('company_settings'))
            except Exception as e:
                print(f"Error updating company name: {e}")
                flash(f"Error updating company name: {str(e)}", 'danger')
                db.session.rollback()
        else:
            flash("Company name cannot be empty.", 'danger')
    
    print(f"Company name before rendering: {company.name}") # Debug print
    return render_template('company_settings.html', company=company)

@app.route('/debug_set_company_name/<name>')
def debug_set_company_name(name):
    company = Company.query.first()
    if not company:
        company = Company(name="Default Company")
        db.session.add(company)
        db.session.commit()
    
    company.name = name
    db.session.commit()
    return f"Company name set to: {name}"

@app.route('/test_company_form')
def test_company_form():
    return render_template('test_company_form.html')

@app.route('/test_invoice_form')
def test_invoice_form():
    return render_template('test_form.html')

@app.route('/test_simple')
def test_simple_forms():
    return render_template('simple_test.html')

@app.route('/simple_login')
def simple_login_page():
    return render_template('simple_login.html')

@app.route('/simple_signup')
def simple_signup_page():
    return render_template('simple_signup.html')



if __name__ == '__main__':
    print('About to start Flask app...')
    with app.app_context():
        print("Creating database tables if they don't exist...")
        db.create_all()
        print("Database tables checked/created.")
        
        # Initialize default services
        initialize_default_services()
        
        # Create default admin user if none exists
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                password_hash=hash_password('admin123'),
                email='admin@example.com',
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user created (admin/admin123)")
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"Error starting Flask app: {e}")
        import traceback
        traceback.print_exc() 