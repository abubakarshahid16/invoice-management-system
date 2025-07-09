from app import app, ServiceTemplate
from flask import Flask, request
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

@app.route('/test_form', methods=['GET', 'POST'])
def test_form():
    if request.method == 'POST':
        print("=== FORM SUBMISSION TEST ===")
        print(f"Form data: {dict(request.form)}")
        print("Form is working correctly!")
        return f"<h1>SUCCESS!</h1><p>Form data: {dict(request.form)}</p>"
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Form Test</title>
        <style>
            body { font-family: Arial; padding: 50px; }
            form { max-width: 400px; }
            input { margin: 10px 0; padding: 10px; width: 100%; box-sizing: border-box; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>Form Test</h1>
        <form method="POST">
            <input type="text" name="username" placeholder="Test Username" required>
            <input type="password" name="password" placeholder="Test Password" required>
            <button type="submit">Test Submit</button>
        </form>
    </body>
    </html>
    '''

with app.app_context():
    # Test CN Motors categorization
    all_services = ServiceTemplate.query.filter_by(company_type='cn_motors', is_active=True).all()
    
    print("=== CN MOTORS DEBUG ===")
    print(f"Total services: {len(all_services)}")
    
    # Test categorization logic
    services_by_category = {
        'engine': [],
        'brakes': [],
        'suspension': [],
        'electrical': [],
        'cooling': [],
        'parts': []
    }
    
    for service in all_services:
        name_lower = service.service_name.lower()
        print(f"Service: '{service.service_name}' -> '{name_lower}'")
        
        categorized = False
        if any(keyword in name_lower for keyword in ['engine', 'motor', 'oil', 'tune', 'spark']):
            services_by_category['engine'].append(service.service_name)
            print(f"  -> Categorized as ENGINE")
            categorized = True
        elif any(keyword in name_lower for keyword in ['brake', 'pad', 'rotor', 'disc']):
            services_by_category['brakes'].append(service.service_name)
            print(f"  -> Categorized as BRAKES")
            categorized = True
        
        if not categorized:
            services_by_category['parts'].append(service.service_name)
            print(f"  -> Categorized as PARTS (default)")
    
    print("\n=== CATEGORIZATION RESULTS ===")
    for category, services in services_by_category.items():
        print(f"{category}: {len(services)} services")
        for service in services:
            print(f"  - {service}")
    
    # Test class creation
    class RepairOptions:
        def __init__(self, categories):
            for key, value in categories.items():
                setattr(self, key, value)
    
    repair_options = RepairOptions(services_by_category)
    print(f"\n=== CLASS TEST ===")
    print(f"repair_options.engine: {len(repair_options.engine)} items")
    print(f"repair_options.brakes: {len(repair_options.brakes)} items")

if __name__ == '__main__':
    app.run(debug=True, port=5001) 