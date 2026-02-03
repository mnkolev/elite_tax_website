"""
Elite Tax & Finance - File Upload API (Fixed Version)
Handles file uploads from your website and processes them for ProConnect
"""

from flask import Flask, request, jsonify, render_template
import json
import os
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

@app.route('/api/get-folder-structure/<complexity_tier>')
def get_folder_structure(complexity_tier):
    """Get folder structure for a complexity tier"""
    try:
        # Define the new hierarchical structure directly
        structures = {
            "Easy": {
                "tier_folder": "Easy Tier Clients",
                "document_folders": ["W-2 Forms", "Standard Deduction", "Basic Credits", "Auto-Processed"],
                "description": "Simple returns with minimal documentation",
                "automation_level": "90%",
                "hierarchy": "Tier > Client > Document Type"
            },
            "Medium": {
                "tier_folder": "Medium Tier Clients",
                "document_folders": ["W-2 Forms", "Itemized Deductions", "Investment Income", "Education Credits", "CPA Review Required"],
                "description": "Moderate complexity requiring CPA review",
                "automation_level": "70%",
                "hierarchy": "Tier > Client > Document Type"
            },
            "Hard": {
                "tier_folder": "Hard Tier Clients",
                "document_folders": ["Multi-State Returns", "Partnership K-1s", "Rental Property", "Foreign Assets", "Complex Deductions", "CPA Preparation"],
                "description": "Complex returns requiring full CPA preparation",
                "automation_level": "30%",
                "hierarchy": "Tier > Client > Document Type"
            }
        }
        
        structure = structures.get(complexity_tier, structures["Easy"])
        
        return jsonify({
            'success': True,
            'structure': structure
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/upload-demo')
def upload_demo():
    """Demo page for file uploads"""
    return render_template('upload_demo.html')

@app.route('/api/upload-documents', methods=['POST'])
def upload_documents():
    """Handle document uploads from your website"""
    try:
        # Get client information
        client_id = request.form.get('client_id')
        complexity_tier = request.form.get('complexity_tier')
        
        if not client_id or not complexity_tier:
            return jsonify({
                'success': False,
                'error': 'Missing client_id or complexity_tier'
            }), 400
        
        # Get uploaded files
        files = request.files.getlist('documents')
        
        if not files:
            return jsonify({
                'success': False,
                'error': 'No files uploaded'
            }), 400
        
        # Simulate processing (replace with actual processing)
        result = {
            'client_id': client_id,
            'complexity_tier': complexity_tier,
            'total_files': len(files),
            'successful_uploads': len(files),
            'failed_uploads': 0,
            'folder_structure': {
                "tier_folder": f"{complexity_tier} Tier Clients",
                "document_folders": ["W-2 Forms", "Standard Deduction", "Basic Credits"],
                "description": f"{complexity_tier} complexity tier",
                "automation_level": "90%" if complexity_tier == "Easy" else "70%" if complexity_tier == "Medium" else "30%",
                "hierarchy": "Tier > Client > Document Type"
            }
        }
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5004)
