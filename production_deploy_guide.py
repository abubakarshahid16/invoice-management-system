#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PRODUCTION DEPLOYMENT GUIDE - Invoice Management System
How to deploy your app securely for commercial use
"""

# ===================================================
# STEP 1: SECURITY IMPROVEMENTS FOR PRODUCTION
# ===================================================

import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import secrets

# 1.1: Secure Configuration
class ProductionConfig:
    """Production configuration with security settings"""
    
    # Generate secure secret key
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # Database - Use PostgreSQL for production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://username:password@localhost/invoice_db'
    
    # Security settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True  # Prevent XSS
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    
    # Email configuration for notifications
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

# 1.2: Replace simple password hashing
def secure_hash_password(password):
    """Use werkzeug's secure password hashing"""
    return generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

def verify_password(password, password_hash):
    """Verify password securely"""
    return check_password_hash(password_hash, password)

# 1.3: Add rate limiting
def setup_rate_limiting(app):
    """Add rate limiting to prevent abuse"""
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=["1000 per hour", "100 per minute"]
    )
    
    # Specific limits for sensitive endpoints
    @limiter.limit("5 per minute")
    def login_rate_limit():
        pass
    
    @limiter.limit("10 per minute") 
    def signup_rate_limit():
        pass
    
    return limiter

# ===================================================
# STEP 2: SUBSCRIPTION SYSTEM INTEGRATION
# ===================================================

# 2.1: User Subscription Model
class Subscription(db.Model):
    """User subscription tracking"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_type = db.Column(db.String(20), nullable=False)  # 'basic', 'pro', 'enterprise'
    status = db.Column(db.String(20), default='active')  # 'active', 'cancelled', 'expired'
    current_period_start = db.Column(db.DateTime, nullable=False)
    current_period_end = db.Column(db.DateTime, nullable=False)
    stripe_subscription_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 2.2: Usage Tracking
class UsageMetric(db.Model):
    """Track user usage for billing"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    metric_type = db.Column(db.String(50))  # 'invoices_created', 'pdf_downloads'
    count = db.Column(db.Integer, default=0)
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)

# 2.3: Plan Limits Check
def check_plan_limits(user_id, action_type):
    """Check if user can perform action based on their plan"""
    user = User.query.get(user_id)
    subscription = Subscription.query.filter_by(user_id=user_id, status='active').first()
    
    if not subscription:
        return False, "No active subscription"
    
    # Define plan limits
    plan_limits = {
        'basic': {'invoices_per_month': 50, 'companies': 1},
        'pro': {'invoices_per_month': -1, 'companies': 3},  # -1 = unlimited
        'enterprise': {'invoices_per_month': -1, 'companies': -1}
    }
    
    limits = plan_limits.get(subscription.plan_type, plan_limits['basic'])
    
    if action_type == 'create_invoice':
        if limits['invoices_per_month'] == -1:
            return True, "Unlimited"
        
        # Check current month usage
        from datetime import datetime, timedelta
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        usage = UsageMetric.query.filter_by(
            user_id=user_id, 
            metric_type='invoices_created',
            period_start=start_of_month
        ).first()
        
        current_count = usage.count if usage else 0
        if current_count >= limits['invoices_per_month']:
            return False, f"Monthly limit of {limits['invoices_per_month']} invoices reached"
    
    return True, "OK"

# ===================================================
# STEP 3: PAYMENT INTEGRATION (STRIPE)
# ===================================================

import stripe

def setup_stripe():
    """Configure Stripe for payments"""
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

def create_checkout_session(user_id, plan_type):
    """Create Stripe checkout session for subscription"""
    
    # Plan pricing (in cents)
    plan_prices = {
        'basic': 1900,    # $19.00
        'pro': 4900,      # $49.00
        'enterprise': 9900 # $99.00
    }
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'Invoice Pro - {plan_type.title()} Plan',
                    },
                    'unit_amount': plan_prices[plan_type],
                    'recurring': {
                        'interval': 'month',
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://yourdomain.com/subscription/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://yourdomain.com/subscription/cancel',
            client_reference_id=str(user_id),
        )
        return checkout_session
    except Exception as e:
        print(f"Error creating checkout session: {e}")
        return None

# ===================================================
# STEP 4: MULTI-TENANT ARCHITECTURE
# ===================================================

class Organization(db.Model):
    """Multi-tenant organization support"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subdomain = db.Column(db.String(50), unique=True)  # company.yourdomain.com
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'))
    settings = db.Column(db.JSON)  # Store custom settings
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def get_current_organization():
    """Get organization from subdomain or session"""
    from flask import request
    
    # Check subdomain
    host = request.host
    if '.' in host:
        subdomain = host.split('.')[0]
        org = Organization.query.filter_by(subdomain=subdomain).first()
        if org:
            return org
    
    # Fallback to session
    org_id = session.get('organization_id')
    if org_id:
        return Organization.query.get(org_id)
    
    return None

# ===================================================
# STEP 5: DEPLOYMENT CONFIGURATION
# ===================================================

# Dockerfile for containerized deployment
DOCKERFILE_CONTENT = '''
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:5000/health || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
'''

# docker-compose.yml for production
DOCKER_COMPOSE_CONTENT = '''
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/invoice_db
      - SECRET_KEY=${SECRET_KEY}
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=invoice_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
'''

# ===================================================
# STEP 6: MONITORING AND ANALYTICS
# ===================================================

def setup_analytics():
    """Setup user analytics and monitoring"""
    
    # Track user actions
    def track_event(user_id, event_type, properties=None):
        """Track user events for analytics"""
        event = UserEvent(
            user_id=user_id,
            event_type=event_type,
            properties=properties or {},
            timestamp=datetime.utcnow()
        )
        db.session.add(event)
        db.session.commit()
    
    # Revenue tracking
    def track_revenue(user_id, amount, plan_type):
        """Track revenue for reporting"""
        revenue = RevenueEvent(
            user_id=user_id,
            amount=amount,
            plan_type=plan_type,
            timestamp=datetime.utcnow()
        )
        db.session.add(revenue)
        db.session.commit()

if __name__ == "__main__":
    print("Production Deployment Guide Created!")
    print("Next Steps:")
    print("1. Set up production database (PostgreSQL)")
    print("2. Configure Stripe payments")
    print("3. Set up monitoring and logging")
    print("4. Deploy to cloud provider (AWS/DigitalOcean/Heroku)")
    print("5. Set up CI/CD pipeline")
    print("6. Launch marketing website") 