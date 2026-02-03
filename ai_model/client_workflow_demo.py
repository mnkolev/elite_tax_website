"""
Elite Tax & Finance - Client Workflow Demo
Shows how client-side and admin-side apps interact
"""

from flask import Flask, request, jsonify, render_template
import json
from datetime import datetime

app = Flask(__name__)

# Enhanced client data with more realistic examples
CLIENTS = {
    "CLIENT_001": {
        "name": "John Smith",
        "email": "john@email.com",
        "complexity_tier": "Easy",
        "status": "Documents Uploaded",
        "upload_date": "2024-01-15",
        "documents": {
            "W-2 Forms": ["W-2_CompanyA_2024.pdf"],
            "Standard Deduction": ["Property_Tax_2024.pdf"],
            "Basic Credits": ["Child_Care_Receipts.pdf"]
        },
        "proconnect_status": "Ready for Review",
        "automation_level": "90%",
        "estimated_completion": "1-2 days"
    },
    "CLIENT_002": {
        "name": "Sarah Johnson", 
        "email": "sarah@email.com",
        "complexity_tier": "Medium",
        "status": "Processing",
        "upload_date": "2024-01-14",
        "documents": {
            "W-2 Forms": ["W-2_CompanyB_2024.pdf"],
            "Itemized Deductions": ["Mortgage_Statement_2024.pdf", "Charitable_Donations.pdf"],
            "Investment Income": ["1099-INT_Bank.pdf", "1099-DIV_Vanguard.pdf", "Robinhood_Statement_2024.pdf"],
            "Education Credits": ["1098-T_University.pdf"]
        },
        "proconnect_status": "CPA Review Required",
        "automation_level": "70%",
        "estimated_completion": "3-5 days"
    },
    "CLIENT_003": {
        "name": "Mike Chen",
        "email": "mike@email.com", 
        "complexity_tier": "Hard",
        "status": "Documents Uploaded",
        "upload_date": "2024-01-13",
        "documents": {
            "Multi-State Returns": ["CA_State_Return.pdf", "NY_State_Return.pdf"],
            "Partnership K-1s": ["K-1_Partnership_ABC.pdf"],
            "Rental Property": ["Rental_Income_Statement.pdf", "Property_Expenses.pdf"],
            "Foreign Assets": ["FBAR_Report.pdf"],
            "Complex Deductions": ["Business_Expenses_2024.pdf"]
        },
        "proconnect_status": "Full CPA Preparation",
        "automation_level": "30%",
        "estimated_completion": "7-14 days"
    },
    "CLIENT_004": {
        "name": "Lisa Garcia",
        "email": "lisa@email.com",
        "complexity_tier": "Easy",
        "status": "Ready for Review",
        "upload_date": "2024-01-12",
        "documents": {
            "W-2 Forms": ["W-2_CompanyC_2024.pdf"],
            "Standard Deduction": ["Property_Tax_2024.pdf"],
            "Basic Credits": ["Child_Care_Receipts.pdf", "Education_Expenses.pdf"]
        },
        "proconnect_status": "Auto-Processed",
        "automation_level": "90%",
        "estimated_completion": "1-2 days"
    },
    "CLIENT_005": {
        "name": "David Wilson",
        "email": "david@email.com",
        "complexity_tier": "Medium",
        "status": "CPA Review",
        "upload_date": "2024-01-11",
        "documents": {
            "W-2 Forms": ["W-2_CompanyD_2024.pdf"],
            "Itemized Deductions": ["Mortgage_Statement_2024.pdf", "Property_Tax_2024.pdf"],
            "Investment Income": ["Schwab_Statement_2024.pdf", "Fidelity_1099_2024.pdf"],
            "Education Credits": ["1098-T_College.pdf"],
            "CPA Review Required": ["Investment_Summary_2024.pdf"]
        },
        "proconnect_status": "Under Review",
        "automation_level": "70%",
        "estimated_completion": "3-5 days"
    },
    "CLIENT_006": {
        "name": "Jennifer Brown",
        "email": "jennifer@email.com",
        "complexity_tier": "Hard",
        "status": "Initial Review",
        "upload_date": "2024-01-10",
        "documents": {
            "Multi-State Returns": ["TX_State_Return.pdf", "CA_State_Return.pdf"],
            "Partnership K-1s": ["K-1_LLC_XYZ.pdf", "K-1_Partnership_DEF.pdf"],
            "Rental Property": ["Rental_Income_2024.pdf", "Property_Management_Fees.pdf"],
            "Foreign Assets": ["FBAR_Report_2024.pdf", "Foreign_Bank_Statement.pdf"],
            "Complex Deductions": ["Business_Expenses_2024.pdf", "Home_Office_Expenses.pdf"],
            "CPA Preparation": ["Tax_Planning_Notes.pdf"]
        },
        "proconnect_status": "Complex Analysis",
        "automation_level": "30%",
        "estimated_completion": "7-14 days"
    }
}

@app.route('/')
def index():
    """Main dashboard showing all clients"""
    return render_template('admin_dashboard.html', clients=CLIENTS)

@app.route('/client/<client_id>')
def client_detail(client_id):
    """Individual client detail page"""
    client = CLIENTS.get(client_id)
    if not client:
        return "Client not found", 404
    
    return render_template('client_detail.html', client_id=client_id, client=client)

@app.route('/proconnect-view/<client_id>')
def proconnect_view(client_id):
    """Simulate what ProConnect would look like"""
    client = CLIENTS.get(client_id)
    if not client:
        return "Client not found", 404
    
    return render_template('proconnect_simulation.html', client_id=client_id, client=client)

@app.route('/api/client-status/<client_id>')
def get_client_status(client_id):
    """Get client status for API"""
    client = CLIENTS.get(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    
    return jsonify({
        "success": True,
        "client": client
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)
