from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
import os

def generate_invoice_pdf(filename, data):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    margin = 50
    
    # Colors
    blue = colors.HexColor('#15395b')
    red = colors.HexColor('#c0392b')
    
    # Title: RECEIPT
    c.setFont('Helvetica-Bold', 48)
    c.setFillColor(blue)
    c.drawString(margin, height - 80, 'RECEIPT')
    
    # Wrench icon placeholder (simple text)
    c.setFont('Helvetica', 24)
    c.setFillColor(colors.gray)
    c.drawString(width - margin - 60, height - 80, '🔧')
    
    # Company Info
    y = height - 140
    c.setFont('Helvetica-Bold', 14)
    c.setFillColor(colors.black)
    c.drawString(margin, y, data['company']['name'])
    
    c.setFont('Helvetica', 12)
    for line in data['company']['address_lines']:
        y -= 18
        c.drawString(margin, y, line)
    
    for phone in data['company'].get('phones', []):
        y -= 18
        c.drawString(margin, y, f"Tell {phone}")
    
    # Bill To and Receipt Number
    y -= 50
    c.setFont('Helvetica-Bold', 14)
    c.setFillColor(blue)
    c.drawString(margin, y, 'BILL TO')
    c.setFont('Helvetica', 12)
    c.setFillColor(colors.black)
    c.drawString(margin, y - 20, data['customer']['name'])
    
    # Receipt Number (right aligned)
    c.setFont('Helvetica-Bold', 14)
    c.setFillColor(blue)
    c.drawRightString(width - margin, y, 'RECEIPT #')
    c.setFont('Helvetica-Bold', 18)
    c.setFillColor(colors.black)
    c.drawRightString(width - margin, y - 25, str(data['receipt_number']))
    
    # Table Header
    y -= 70
    c.setStrokeColor(red)
    c.setLineWidth(3)
    c.line(margin, y, width - margin, y)
    
    c.setFont('Helvetica-Bold', 16)
    c.setFillColor(blue)
    c.drawString(margin, y - 25, 'DESCRIPTION')
    c.drawRightString(width - margin, y - 25, 'AMOUNT')
    
    # Items
    y -= 50
    c.setFont('Helvetica', 14)
    c.setFillColor(colors.black)
    
    for item in data['items']:
        c.drawString(margin, y, item['description'])
        c.drawRightString(width - margin, y, f"{item['amount']:.2f}")
        y -= 25
    
    # Totals section
    y -= 30
    totals_x = width - margin - 200
    
    c.setFont('Helvetica', 14)
    c.drawString(totals_x, y, 'Subtotal')
    c.drawRightString(width - margin, y, f"{data['subtotal']:.2f}")
    
    y -= 20
    c.drawString(totals_x, y, f"Hst {data['hst_rate']:.1f}%")
    c.drawRightString(width - margin, y, f"{data['hst_amount']:.2f}")
    
    # Total line
    y -= 25
    c.setStrokeColor(blue)
    c.setLineWidth(2)
    c.line(totals_x, y + 5, width - margin, y + 5)
    
    c.setFont('Helvetica-Bold', 18)
    c.setFillColor(blue)
    c.drawString(totals_x, y - 15, 'TOTAL')
    c.drawRightString(width - margin, y - 15, f"{data['total']:.2f} $")
    
    # Signature line
    y -= 80
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    signature_start = width - margin - 150
    c.line(signature_start, y, width - margin, y)
    
    c.save()

if __name__ == '__main__':
    # Test data matching the simple format
    invoice_data = {
        'company': {
            'name': 'Cn Auto Collision Inc.',
            'address_lines': [
                '1770 Albion Rd,unit 53',
                'Etobicoke,ON M9V 4J9',
            ],
            'phones': ['6474673490', '4166706595']
        },
        'customer': {
            'name': 'Ali shah'
        },
        'receipt_number': 101,
        'items': [
            {'description': 'oil change', 'amount': 80.00},
        ],
        'subtotal': 80.00,
        'hst_rate': 13.0,
        'hst_amount': 10.40,
        'total': 90.40
    }
    generate_invoice_pdf('invoice.pdf', invoice_data)
    print('Simple invoice PDF generated as invoice.pdf') 