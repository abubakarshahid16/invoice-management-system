🚗 MECHANIC SHOP INVOICE MANAGEMENT SYSTEM
============================================

📋 SYSTEM REQUIREMENTS:
- Windows 10 or later
- Python 3.6 or later
- Internet connection (for initial setup only)

📦 WHAT'S INCLUDED:
- simple_app.py (Main application)
- templates/ (Web interface files)
- static/ (CSS, JavaScript, images)
- data.json (Database file - will be created automatically)
- requirements.txt (Python dependencies)
- start_server.bat (Easy startup script)
- install_dependencies.bat (Dependency installer)
- README_DEPLOYMENT.txt (This file)

🚀 QUICK START GUIDE:
=====================

STEP 1: Install Python
----------------------
1. Go to https://www.python.org/downloads/
2. Download Python 3.8 or later for Windows
3. Run the installer
4. IMPORTANT: Check "Add Python to PATH" during installation
5. Click "Install Now"

STEP 2: Install Dependencies
----------------------------
1. Double-click "install_dependencies.bat"
2. Wait for installation to complete
3. Press any key when finished

STEP 3: Start the System
------------------------
1. Double-click "start_server.bat"
2. The system will start and show a message like:
   "Running on http://192.168.1.8:5000"
3. Open your web browser
4. Go to: http://localhost:5000

🌐 NETWORK ACCESS (For Multiple Computers):
===========================================

To access from other computers on the same network:

1. Find your computer's IP address:
   - Open Command Prompt
   - Type: ipconfig
   - Look for "IPv4 Address" (e.g., 192.168.1.8)

2. From other computers, open browser and go to:
   http://[YOUR_IP_ADDRESS]:5000
   Example: http://192.168.1.8:5000

📁 FOLDER STRUCTURE:
====================
MechanicShop/
├── simple_app.py          (Main application)
├── templates/             (Web pages)
│   ├── base.html
│   ├── index.html
│   ├── customers.html
│   ├── vehicles.html
│   ├── services.html
│   ├── invoices.html
│   └── view_invoice.html
├── static/                (CSS, JavaScript)
├── data.json             (Your data - created automatically)
├── requirements.txt      (Dependencies list)
├── start_server.bat      (Start the system)
├── install_dependencies.bat (Install dependencies)
└── README_DEPLOYMENT.txt (This file)

🔧 TROUBLESHOOTING:
===================

Problem: "python is not recognized"
Solution: 
- Reinstall Python and make sure to check "Add Python to PATH"
- Or restart your computer after installing Python

Problem: "No module named 'flask'"
Solution:
- Run "install_dependencies.bat" again
- Or manually run: pip install -r requirements.txt

Problem: "Port 5000 is already in use"
Solution:
- Close other applications that might be using port 5000
- Or edit simple_app.py and change port number

Problem: Can't access from other computers
Solution:
- Check Windows Firewall settings
- Make sure all computers are on the same network
- Try using the computer's IP address instead of localhost

💾 BACKUP YOUR DATA:
====================
- Your data is stored in "data.json"
- Copy this file regularly to backup your information
- To restore, simply replace the data.json file

🔄 UPDATING THE SYSTEM:
=======================
1. Stop the server (Ctrl+C)
2. Replace the files with new versions
3. Restart the server

📞 SUPPORT:
===========
If you encounter any issues:
1. Check this README file
2. Make sure Python is installed correctly
3. Try running install_dependencies.bat again
4. Contact your system administrator

🎯 FEATURES INCLUDED:
=====================
✅ Customer Management
✅ Vehicle Management  
✅ Service Management
✅ Invoice Creation
✅ Invoice Status Updates (Pending/Paid/Overdue/Cancelled)
✅ Print Invoices
✅ Network Access
✅ Data Backup

============================================
🚗 MECHANIC SHOP INVOICE SYSTEM - READY TO USE!
============================================ 