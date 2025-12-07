import os
from weasyprint import HTML
from io import BytesIO

# --- CONFIGURATION ---
OUTPUT_FILE = "filled_order_invoice.pdf"
# IMPORTANT: Place your logo file (e.g., 'angel_logo.png') in the same directory.
LOGO_FILE = "logo-angel (1).png" 
BASE_URL = os.path.dirname(os.path.abspath(__file__))

# --- MOCK DATA (WooCommerce Webhook Simulation) ---
MOCK_DATA = [{
    "body": {
        "id": 2506,
        "number": "2506",
        "date_created": "2025-11-21T20:20:21",
        "total": "16.00",
        "shipping_total": "5.00",
        "total_tax": "1.00",
        "billing": {
            "first_name": "Augusto",
            "last_name": "Castro",
            "company": "My Company LTD",
            "email": "augusto.webdeveloping@gmail.com",
            "phone": "5527995271631",
            "address_1": "Main Street, 123",
            "address_2": "Apt 101",
            "city": "Vila Velha",
            "state": "ES",
            "postcode": "29100-000",
        },
        "line_items": [
            {
                "name": "Test Product (Item 1)",
                "quantity": 1,
                "total": "10.00",
            },
            {
                "name": "Additional Service Fee",
                "quantity": 1,
                "total": "6.00",
            }
        ]
    }
}]


def format_date(date_str: str) -> str:
    """Formats the ISO date (YYYY-MM-DDTHH:mm:ss) to MM/DD/YYYY."""
    if not date_str:
        return "N/A"
    try:
        date_part = date_str.split('T')[0]
        year, month, day = date_part.split('-')
        # US/English standard is usually MM/DD/YYYY
        return f"{month}/{day}/{year}" 
    except Exception:
        return date_str


def build_html_template(data_list: list) -> str:
    """
    Generates the HTML string with the invoice layout, filling in the JSON data.
    """
    if not data_list or not isinstance(data_list[0], dict):
        raise ValueError("Invalid input data structure.")
        
    body = data_list[0].get("body", {}) 

    # --- Data Extraction ---
    billing = body.get("billing", {})
    line_items = body.get("line_items", [])
    
    # Currency symbol (assuming USD or similar, based on mock data)
    currency = "$" 

    # 1. Build the Item Table Rows
    items_html = ""
    for item in line_items:
        items_html += f"""
        <tr>
            <td class="qty">{item.get('quantity', 1)}</td>
            <td class="item-name">{item.get('name', 'N/A')}</td>
            <td class="notes"></td> 
            <td class="price">{currency} {float(item.get('total', '0.00')):.2f}</td>
        </tr>
        """
        
    # 2. Styling (CSS)
    style = """
    <style>
        @page { size: A4; margin: 1cm; }
        body { font-family: Arial, sans-serif; font-size: 10pt; line-height: 1.4; color: #333; }
        h1, h2 { margin-top: 0; }
        .header { overflow: hidden; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #ccc; }
        .logo { float: left; width: 80px; height: auto; margin-right: 20px; }
        .invoice-info { float: right; text-align: right; }
        .details h2 { border-bottom: 1px solid #eee; padding-bottom: 5px; font-size: 12pt; }
        .details p { margin: 2px 0; }
        
        .items-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        .items-table th, .items-table td { border: 1px solid #eee; padding: 8px; text-align: left; }
        .items-table th { background-color: #f4f4f4; }
        .qty { width: 5%; text-align: center; }
        .price { width: 15%; text-align: right; }
        
        .total-summary { 
            width: 300px; 
            margin-top: 20px; 
            float: right; 
            border: 1px solid #ccc;
            padding: 10px;
        }
        .total-summary table { width: 100%; border-collapse: collapse; }
        .total-summary tr td { padding: 5px; border: none; }
        .total-summary .label { font-weight: bold; }
        .total-summary .value { text-align: right; }
    </style>
    """
    
    # 3. Final HTML Assembly
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Order Invoice #{body.get('number', 'N/A')}</title>
        {style}
    </head>
    <body>
        <div class="container">
            
            <div class="header">
                <img src="{LOGO_FILE}" class="logo" alt="Company Logo">
                
                <div class="invoice-info">
                    <h1>INVOICE / ORDER NOTE</h1>
                    <p><strong>Order #</strong>: {body.get('number', body.get('id', 'N/A'))}</p>
                    <p><strong>Date</strong>: {format_date(body.get('date_created', ''))}</p>
                    <p><strong>Status</strong>: {body.get('status', 'N/A').upper()}</p>
                </div>
            </div>
            
            <div style="clear: both;"></div> 

            <div class="details">
                <h2>Customer Details</h2>
                <p><strong>Name:</strong> {billing.get('first_name', '')} {billing.get('last_name', '')} ({billing.get('company', '')})</p>
                <p><strong>Email:</strong> {billing.get('email', 'N/A')}</p>
                <p><strong>Phone:</strong> {billing.get('phone', 'N/A')}</p>
                <p><strong>Address:</strong> {billing.get('address_1', '')}, {billing.get('city', '')} - {billing.get('state', '')} CEP: {billing.get('postcode', '')}</p>
            </div>
            
            <h2>Order Items</h2>
            
            <table class="items-table">
                <thead>
                    <tr>
                        <th class="qty">QTY</th>
                        <th class="item-name">ITEM</th>
                        <th class="notes">NOTES</th>
                        <th class="price">PRICE</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>
            
            <div class="total-summary">
                <table>
                    <tr>
                        <td class="label">Sub Total:</td>
                        <td class="value">{currency} {body.get('total', '0.00')}</td>
                    </tr>
                    <tr>
                        <td class="label">Shipping:</td>
                        <td class="value">{currency} {body.get('shipping_total', '0.00')}</td>
                    </tr>
                    <tr>
                        <td class="label">Tax:</td>
                        <td class="value">{currency} {body.get('total_tax', '0.00')}</td>
                    </tr>
                    <tr>
                        <td class="label">GRAND TOTAL:</td>
                        <td class="value"><strong>{currency} {body.get('total', '0.00')}</strong></td>
                    </tr>
                </table>
            </div>
            <div style="clear: both;"></div> 
            
            <div style="margin-top: 50px; font-size: 8pt; text-align: center;">
                <p>Thank you for your business. Please contact us for any questions regarding this invoice.</p>
            </div>

        </div>
    </body>
    </html>
    """
    return html_content


def generate_pdf_from_html():
    """
    Main function that generates HTML from MOCK_DATA and saves it as a PDF.
    """
    print("Starting local PDF generation...")
    
    # Check if logo file exists for better error messages
    if not os.path.exists(os.path.join(BASE_URL, LOGO_FILE)):
        print(f"⚠️ WARNING: Logo file '{LOGO_FILE}' not found. The image link in the PDF will be broken.")

    try:
        # 1. Generate filled HTML
        html_content = build_html_template(MOCK_DATA)
        
        # 2. Convert HTML to PDF using WeasyPrint
        # BASE_URL is crucial for finding the local image file (logo)
        html = HTML(string=html_content, base_url=BASE_URL)
        
        # 3. Save the PDF to disk
        html.write_pdf(OUTPUT_FILE)
            
        print(f"\n🎉 SUCCESS! The PDF file has been created at: {os.path.abspath(OUTPUT_FILE)}")

    except Exception as e:
        print(f"\n❌ FATAL ERROR during PDF generation:")
        print(f"Detail: {e}")
        print("\nCHECK DEPENDENCIES: Ensure 'pip install weasyprint' was successful, and if using Linux/macOS, check system libraries (Pango, Cairo).")


if __name__ == "__main__":
    generate_pdf_from_html()