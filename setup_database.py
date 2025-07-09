#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database Setup Script for Invoice Management System
This script will create tables and initialize the database with proper company data
"""

import os
import sys
import json
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Customer, Vehicle, Invoice, InvoiceItem, Company, hash_password

def setup_database(fresh_start=False):
    """Setup the database with all necessary tables and initial data"""
    with app.app_context():
        try:
            if fresh_start:
                print("Dropping all existing tables...")
                db.drop_all()
            
            # Create all tables
            print("Creating database tables...")
            db.create_all()
            print("Database tables created successfully.")
            
            # Setup company data
            setup_company_data()
            
            # Setup default admin user
            setup_admin_user()
            
            # Load existing data from JSON
            load_existing_data()
            
            db.session.commit()
            print("\nDatabase setup completed successfully!")
            print("You can now start the application with: python app.py")
            print("Default login: admin / admin123")
            
        except Exception as e:
            print(f"Error setting up database: {e}")
            db.session.rollback()
            raise

def setup_company_data():
    """Setup company data matching the receipt format"""
    company = Company.query.first()
    if not company:
        company = Company(
            name="Cn Auto Collision Inc.",
            address="1770 Albion Rd,unit 53",
            city="Etobicoke",
            postal_code="ON M9V 4J9",
            phone1="6474673490",
            phone2="4166706595",
            services="Auto Collision Repair Services"
        )
        db.session.add(company)
        print("✓ Company data created: Cn Auto Collision Inc.")
    else:
        # Update existing company with proper data
        company.name = "Cn Auto Collision Inc."
        company.address = "1770 Albion Rd,unit 53"
        company.city = "Etobicoke"
        company.postal_code = "ON M9V 4J9"
        company.phone1 = "6474673490"
        company.phone2 = "4166706595"
        company.services = "Auto Collision Repair Services"
        print("✓ Company data updated: Cn Auto Collision Inc.")

def setup_admin_user():
    """Setup default admin user"""
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
        print("✓ Admin user created (username: admin, password: admin123)")
    else:
        print("✓ Admin user already exists")

def load_existing_data():
    """Load existing data from data.json if it exists"""
    if not os.path.exists('data.json'):
        print("✓ No existing data.json found - starting with clean database")
        return
    
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
        
        # Load customers
        customers_added = 0
        for customer_data in data.get('customers', []):
            existing = Customer.query.filter_by(name=customer_data['name']).first()
            if not existing:
                customer = Customer(
                    name=customer_data['name'],
                    phone=customer_data['phone'],
                    email=customer_data.get('email', ''),
                    created_at=datetime.strptime(customer_data['created_at'], '%Y-%m-%dT%H:%M:%S.%f') if 'created_at' in customer_data else datetime.now()
                )
                db.session.add(customer)
                customers_added += 1
        
        if customers_added > 0:
            print(f"✓ Added {customers_added} customers from data.json")
        
        # Load vehicles
        vehicles_added = 0
        for vehicle_data in data.get('vehicles', []):
            customer = Customer.query.filter_by(id=vehicle_data['customer_id']).first()
            if customer:
                existing = Vehicle.query.filter_by(
                    customer_id=customer.id,
                    make=vehicle_data['make'],
                    model=vehicle_data['model'],
                    year=vehicle_data['year']
                ).first()
                if not existing:
                    vehicle = Vehicle(
                        customer_id=customer.id,
                        year=vehicle_data['year'],
                        make=vehicle_data['make'],
                        model=vehicle_data['model'],
                        license_plate=vehicle_data.get('plate', '')
                    )
                    db.session.add(vehicle)
                    vehicles_added += 1
        
        if vehicles_added > 0:
            print(f"✓ Added {vehicles_added} vehicles from data.json")
        
        # Load invoices with proper calculations
        invoices_added = 0
        for invoice_data in data.get('invoices', []):
            existing = Invoice.query.filter_by(invoice_number=invoice_data['invoice_number']).first()
            if not existing:
                # Calculate proper totals
                subtotal = invoice_data.get('subtotal', 0)
                tax_rate = invoice_data.get('tax_rate', 13.0)
                tax_amount = subtotal * (tax_rate / 100)
                total = subtotal + tax_amount
                
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
                    created_at=datetime.strptime(invoice_data['created_at'], '%Y-%m-%dT%H:%M:%S.%f') if 'created_at' in invoice_data else datetime.now()
                )
                db.session.add(invoice)
                db.session.flush()  # Get the invoice ID
                
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
                    
                    unit_price = item_data.get('unit_price', 0)
                    quantity = item_data.get('quantity', 1)
                    total_price = unit_price * quantity
                    
                    item = InvoiceItem(
                        invoice_id=invoice.id,
                        description=service_name,
                        quantity=quantity,
                        unit_price=unit_price,
                        total=total_price
                    )
                    db.session.add(item)
                
                invoices_added += 1
        
        if invoices_added > 0:
            print(f"✓ Added {invoices_added} invoices from data.json")
            
        print("✓ Existing data loaded successfully")
        
    except Exception as e:
        print(f"Warning: Error loading data.json: {e}")

if __name__ == '__main__':
    print("Invoice Management System - Database Setup")
    print("=" * 50)
    
    # Ask if user wants a fresh start
    if len(sys.argv) > 1 and sys.argv[1] == '--fresh':
        fresh_start = True
        print("Fresh database setup requested...")
    else:
        response = input("Do you want to start with a fresh database? (y/N): ")
        fresh_start = response.lower().startswith('y')
    
    setup_database(fresh_start) 