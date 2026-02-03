"""
Elite Tax & Finance - Smart Upload API
Integrates intelligent document classification and year-over-year tracking
"""

from flask import Flask, request, jsonify, render_template
import json
import os
from datetime import datetime
from document_processor import DocumentProcessor
from document_tracker import DocumentTracker
from tax_automation_system import TaxAutomationSystem

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

# Initialize systems
tax_system = TaxAutomationSystem()
document_processor = DocumentProcessor()
document_tracker = DocumentTracker()

@app.route('/')
def index():
    """Smart upload dashboard"""
    return render_template('smart_upload_dashboard.html')

@app.route('/api/smart-upload', methods=['POST'])
def smart_upload():
    """Handle smart document uploads with automatic classification"""
    try:
        # Get client information
        client_id = request.form.get('client_id')
        client_name = request.form.get('client_name', 'Unknown Client')
        complexity_tier = request.form.get('complexity_tier')
        tax_year = int(request.form.get('tax_year', datetime.now().year))
        
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
        
        # Get or create client document profile
        profile = document_tracker.get_client_profile(client_id)
        if not profile:
            profile = document_tracker.create_client_profile(
                client_id, client_name, complexity_tier, tax_year
            )
        
        # Process each file with smart classification
        upload_results = []
        classification_results = []
        
        for file in files:
            if file.filename:
                # Save file temporarily
                temp_path = f"temp_{file.filename}"
                file.save(temp_path)
                
                # Smart classification
                document_type = document_processor.document_classifier.classify_document(
                    file.filename, temp_path
                )
                
                # Add to document tracker
                success = document_tracker.add_document(
                    client_id, document_type, file.filename, tax_year
                )
                
                # Determine target folder
                target_folder = document_processor._determine_target_folder(
                    document_type, complexity_tier, client_id, client_name
                )
                
                upload_results.append({
                    'filename': file.filename,
                    'document_type': document_type,
                    'target_folder': target_folder,
                    'upload_success': success
                })
                
                classification_results.append({
                    'filename': file.filename,
                    'classified_as': document_type,
                    'confidence': 'high' if document_type != 'Unknown Document' else 'low'
                })
                
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        # Get updated document requirements
        required_docs = document_tracker.get_required_documents(client_id, tax_year)
        
        return jsonify({
            'success': True,
            'results': {
                'client_id': client_id,
                'client_name': client_name,
                'complexity_tier': complexity_tier,
                'tax_year': tax_year,
                'upload_results': upload_results,
                'classification_results': classification_results,
                'required_documents': required_docs,
                'folder_structure': document_processor._get_folder_structure(complexity_tier)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/client-documents/<client_id>')
def get_client_documents(client_id):
    """Get client's document status and requirements"""
    try:
        tax_year = int(request.args.get('tax_year', datetime.now().year))
        
        # Get client profile
        profile = document_tracker.get_client_profile(client_id)
        if not profile:
            return jsonify({
                'success': False,
                'error': 'Client profile not found'
            }), 404
        
        # Get required documents
        required_docs = document_tracker.get_required_documents(client_id, tax_year)
        
        # Get suggestions for next year
        suggestions = document_tracker.get_document_suggestions(client_id, tax_year + 1)
        
        return jsonify({
            'success': True,
            'client_profile': {
                'client_id': profile.client_id,
                'client_name': profile.client_name,
                'complexity_tier': profile.complexity_tier,
                'last_updated': profile.last_updated
            },
            'required_documents': required_docs,
            'next_year_suggestions': suggestions
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/mark-document-na', methods=['POST'])
def mark_document_na():
    """Mark a document as N/A for a client"""
    try:
        data = request.get_json()
        
        client_id = data.get('client_id')
        document_type = data.get('document_type')
        tax_year = data.get('tax_year', datetime.now().year)
        reason = data.get('reason', 'Not applicable')
        
        if not client_id or not document_type:
            return jsonify({
                'success': False,
                'error': 'Missing client_id or document_type'
            }), 400
        
        success = document_tracker.mark_document_na(
            client_id, document_type, tax_year, reason
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'{document_type} marked as N/A for {tax_year}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to mark document as N/A'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/smart-upload-demo')
def smart_upload_demo():
    """Demo page for smart uploads"""
    return render_template('smart_upload_demo.html')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5006)

