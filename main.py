from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from weasyprint import HTML
from io import BytesIO
import os

app = FastAPI()

# --- CONFIGURATION ---
# IMPORTANT: Place your logo file (e.g., 'angel_logo.png') in the same directory.
LOGO_FILE = "angel_logo.png" 
# BASE_URL não é estritamente necessário para o path do logo no CSS,
# mas é mantido como referência para outros usos.
BASE_URL = os.path.dirname(os.path.abspath(__file__))


def format_date(date_str: str) -> str:
    """Formats the ISO date (YYYY-MM-DDTHH:mm:ss) to MM/DD/YYYY."""
    if not date_str:
        return "N/A"
    try:
        date_part = date_str.split('T')[0]
        year, month, day = date_part.split('-')
        # Standard US/English format
        return f"{month}/{day}/{year}" 
    except Exception:
        return date_str


def build_html_template(data: dict) -> str:
    """
    Generates the HTML string with the invoice layout, filling in the JSON data.
    The function expects the payload structure from n8n (list or dictionary containing the 'body').
    """
    
    # 1. Extract the order body from the payload
    if isinstance(data, list) and data and "body" in data[0]:
        body = data[0]["body"]
    elif "body" in data:
        body = data["body"]
    else:
        # Assume the payload is the body itself if the structure is flat
        body = data

    # --- Data Extraction ---
    billing = body.get("billing", {})
    line_items = body.get("line_items", [])
    
    currency = "$" 
    
    # 🌟 CORREÇÃO: Lógica Condicional para o Nome da Empresa
    # 1. Obter e limpar o nome da empresa
    company_name = billing.get('company', '').strip()
    
    # 2. Criar a string de exibição da empresa (só adiciona (nome) se existir)
    # Exemplo: Se company_name é "Angel's", company_display será " (Angel's)". Se for "", será "".
    company_display = f" ({company_name})" if company_name else ""
    # ----------------------------------------------------------------------
    
    # 2. Build the Item Table Rows
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
        
    # 3. Styling (CSS) - Defines the PDF layout
    # USAMOS A F-STRING AQUI PARA INJETAR O CAMINHO ABSOLUTO DO DOCKER NO CSS
    style = f"""
    <style>
        @page {{ size: A4; margin: 1cm; }}
        body {{ font-family: Arial, sans-serif; font-size: 10pt; line-height: 1.4; color: #333; }}
        h1, h2 {{ margin-top: 0; }}
        .header {{ overflow: hidden; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #ccc; }}
        .logo {{ 
            float: left; 
            width: 80px; 
            height: auto; 
            margin-right: 20px;
            /* CHAVE: Caminho absoluto dentro do container Docker */
            content: url('file:///app/{LOGO_FILE}'); 
        }}
        .invoice-info {{ float: right; text-align: right; }}
        .details h2 {{ border-bottom: 1px solid #eee; padding-bottom: 5px; font-size: 12pt; }}
        .details p {{ margin: 2px 0; }}
        
        .items-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        .items-table th, .items-table td {{ border: 1px solid #eee; padding: 8px; text-align: left; }}
        .items-table th {{ background-color: #f4f4f4; }}
        .qty {{ width: 5%; text-align: center; }}
        .price {{ width: 15%; text-align: right; }}
        
        .total-summary {{ 
            width: 300px; 
            margin-top: 20px; 
            float: right; 
            border: 1px solid #ccc;
            padding: 10px;
        }}
        .total-summary table {{ width: 100%; border-collapse: collapse; }}
        .total-summary tr td {{ padding: 5px; border: none; }}
        .total-summary .label {{ font-weight: bold; }}
        .total-summary .value {{ text-align: right; }}
    </style>
    """
    
    # 4. Final HTML Assembly
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
                <div class="logo"></div>
                
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
                
                <p><strong>Name:</strong> {billing.get('first_name', '')} {billing.get('last_name', '')}{company_display}</p>
                
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


@app.post("/generate-pdf-invoice")
async def generate_pdf_invoice(request: Request):
    """
    Receives the order JSON (WooCommerce/n8n) and returns a filled PDF.
    """
    
    try:
        # Handle JSON body
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Request body must be valid JSON.")

    # 1. Generate the filled HTML string
    try:
        html_content = build_html_template(payload)
    except KeyError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to extract data from JSON. Check the webhook structure (missing key: {e})."
        )
    except Exception as e:
        # Check if the error is related to image loading path issues inside the Docker container
        if 'file not found' in str(e).lower() and LOGO_FILE in str(e):
             raise HTTPException(
                status_code=500,
                detail=f"Error loading logo: {e}. Ensure '{LOGO_FILE}' is available in the container's /app directory."
            )
        raise HTTPException(status_code=500, detail=f"Internal error while building HTML: {e}")

    # 2. Convert HTML to PDF using WeasyPrint (in memory)
    try:
        # Usamos base_url="file:///" para garantir que caminhos absolutos como file:///app/ sejam resolvidos corretamente
        html = HTML(string=html_content, base_url="file:///")
        buf = BytesIO()
        html.write_pdf(buf)
        buf.seek(0)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"WeasyPrint conversion error (PDF): {e}. Verify that WeasyPrint dependencies (Pango, Cairo) are installed."
        )

    # 3. Prepare the response
    if isinstance(payload, list) and payload:
        data_source = payload[0]
    else:
        data_source = payload
        
    order_number = data_source.get("body", {}).get("number", data_source.get("body", {}).get("id", "no_id"))

    filename = f"invoice_order_{order_number}.pdf"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}

    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers=headers,
    )