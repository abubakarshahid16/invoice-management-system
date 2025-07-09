#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Customer, Vehicle, Invoice, InvoiceItem, Company, hash_password

def initialize_database():
    """Initialize the database with tables and sample data"""
    with app.app_context():
        try:
            # Create all tables
            print("Creating database tables...")
            db.create_all()
            print("Database tables created successfully.")
            
            # Check if company already exists
            company = Company.query.first()
            if not company:
                # Create company with data matching the receipt format
                company = Company(
                    name="Cn Auto Collision Inc.",
                    address="1770 Albion Rd,unit 53",
                    city="Etobicoke,ON M9V 4J9",
                    phone1="6474673490",
                    phone2="4166706595",
                    services="Auto Collision Repair Services"
                )
                db.session.add(company)
                print("Company created with receipt format data.")
            
            # Create default admin user if not exists
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    password_hash=hash_password('admin123'),
                    email='admin@cnauto.com',
                    role='admin',
                    company_id='1'
                )
                db.session.add(admin_user)
                print("Admin user created.")
            
            # Load existing data from JSON files if they exist
            load_json_data()
            
            db.session.commit()
            print("Database initialization completed successfully!")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            db.session.rollback()
            raise

def load_json_data():
    """Load data from JSON files into the database"""
    try:
        # Load data.json if it exists
        if os.path.exists('data.json'):
            with open('data.json', 'r') as f:
                data = json.load(f)
            
            # Load customers
            for customer_data in data.get('customers', []):
                existing_customer = Customer.query.filter_by(name=customer_data['name']).first()
                if not existing_customer:
                    customer = Customer(
                        name=customer_data['name'],
                        phone=customer_data['phone'],
                        email=customer_data.get('email', ''),
                        created_at=datetime.fromisoformat(customer_data['created_at']) if 'created_at' in customer_data else datetime.now()
                    )
                    db.session.add(customer)
                    print(f"Added customer: {customer.name}")
            
            # Load vehicles
            for vehicle_data in data.get('vehicles', []):
                existing_vehicle = Vehicle.query.filter_by(
                    make=vehicle_data['make'],
                    model=vehicle_data['model'],
                    year=vehicle_data['year']
                ).first()
                if not existing_vehicle:
                    # Find the customer
                    customer = Customer.query.filter_by(id=vehicle_data['customer_id']).first()
                    if customer:
                        vehicle = Vehicle(
                            customer_id=customer.id,
                            year=vehicle_data['year'],
                            make=vehicle_data['make'],
                            model=vehicle_data['model'],
                            license_plate=vehicle_data.get('plate', '')
                        )
                        db.session.add(vehicle)
                        print(f"Added vehicle: {vehicle.year} {vehicle.make} {vehicle.model}")
            
            # Load invoices
            for invoice_data in data.get('invoices', []):
                existing_invoice = Invoice.query.filter_by(invoice_number=invoice_data['invoice_number']).first()
                if not existing_invoice:
                    # Calculate totals
                    subtotal = invoice_data.get('subtotal', 0)
                    tax_rate = invoice_data.get('tax_rate', 13.0)
                    tax_amount = invoice_data.get('tax_amount', subtotal * (tax_rate / 100))
                    total = invoice_data.get('total', subtotal + tax_amount)
                    
                    invoice = Invoice(
                        invoice_number=invoice_data['invoice_number'],
                        customer_id=invoice_data['customer_id'],
                        vehicle_id=invoice_data.get('vehicle_id'),
                        status=invoice_data.get('status', 'pending'),
                        subtotal=subtotal,
                        tax_rate=tax_rate,
                        tax_amount=tax_amount,
                        total=total,
                        notes=invoice_data.get('notes', ''),
                        created_at=datetime.fromisoformat(invoice_data['created_at']) if 'created_at' in invoice_data else datetime.now()
                    )
                    db.session.add(invoice)
                    
                    # Add invoice items
                    for item_data in invoice_data.get('items', []):
                        # Get service name from services list
                        service_name = "Unknown Service"
                        service_id = item_data.get('service_id')
                        if service_id:
                            for service in data.get('services', []):
                                if service['id'] == service_id:
                                    service_name = service['name']
                                    break
                        
                        item = InvoiceItem(
                            invoice_id=invoice.id,
                            description=service_name,
                            quantity=item_data.get('quantity', 1),
                            unit_price=item_data.get('unit_price', 0),
                            total=item_data.get('unit_price', 0) * item_data.get('quantity', 1)
                        )
                        db.session.add(item)
                    
                    print(f"Added invoice: {invoice.invoice_number}")
            
            print("JSON data loaded successfully.")
    
    except Exception as e:
        print(f"Error loading JSON data: {e}")

def backup_database():
    import shutil
    import datetime
    
    # Create a timestamped backup
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'mechanic_shop_backup_{timestamp}.db'
    
    # Copy the database file
    shutil.copy2('mechanic_shop.db', backup_file)
    print(f"Database backed up to: {backup_file}")

if __name__ == '__main__':
    initialize_database()
    backup_database()
