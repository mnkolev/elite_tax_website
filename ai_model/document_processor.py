"""
Elite Tax & Finance - Document Processing System
Handles file uploads, OCR processing, and ProConnect organization
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import mimetypes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DocumentInfo:
    """Information about an uploaded document"""
    filename: str
    file_path: str
    document_type: str
    file_size: int
    upload_date: datetime
    complexity_tier: str
    target_folder: str
    extracted_data: Dict[str, Any] = None
    validation_status: str = "pending"

@dataclass
class ProcessingResult:
    """Result of document processing"""
    success: bool
    document_info: DocumentInfo
    extracted_data: Dict[str, Any] = None
    error_message: str = None
    proconnect_upload_result: Dict[str, Any] = None

class DocumentProcessor:
    """Main document processing system"""
    
    def __init__(self, upload_directory: str = "uploads", proconnect_integration=None):
        self.upload_directory = upload_directory
        self.proconnect = proconnect_integration
        self.supported_formats = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff']
        self.document_classifier = DocumentClassifier()
        self.ocr_processor = OCRProcessor()
        self.data_extractor = DataExtractor()
        
        # Ensure upload directory exists
        os.makedirs(upload_directory, exist_ok=True)
    
    def process_uploaded_files(self, files: List[Dict[str, Any]], 
                             client_id: str, complexity_tier: str) -> Dict[str, Any]:
        """Process multiple uploaded files for a client"""
        try:
            processing_results = []
            successful_uploads = []
            failed_uploads = []
            
            for file_info in files:
                # Process individual file
                result = self.process_single_file(
                    file_info, client_id, complexity_tier
                )
                
                processing_results.append(result)
                
                if result.success:
                    successful_uploads.append(result.document_info)
                else:
                    failed_uploads.append({
                        'filename': file_info.get('filename'),
                        'error': result.error_message
                    })
            
            # Organize successful documents in ProConnect
            proconnect_organization = None
            if successful_uploads and self.proconnect:
                proconnect_organization = self._organize_in_proconnect(
                    client_id, complexity_tier, successful_uploads
                )
            
            return {
                'client_id': client_id,
                'complexity_tier': complexity_tier,
                'total_files': len(files),
                'successful_uploads': len(successful_uploads),
                'failed_uploads': len(failed_uploads),
                'processing_results': processing_results,
                'proconnect_organization': proconnect_organization,
                'folder_structure': self._get_folder_structure(complexity_tier)
            }
            
        except Exception as e:
            logger.error(f"Error processing uploaded files: {str(e)}")
            return {
                'error': str(e),
                'client_id': client_id,
                'complexity_tier': complexity_tier
            }
    
    def process_single_file(self, file_info: Dict[str, Any], 
                          client_id: str, complexity_tier: str) -> ProcessingResult:
        """Process a single uploaded file"""
        try:
            filename = file_info.get('filename')
            file_content = file_info.get('content')
            
            # Validate file
            if not self._validate_file(filename, file_content):
                return ProcessingResult(
                    success=False,
                    document_info=None,
                    error_message=f"Invalid file: {filename}"
                )
            
            # Save file
            file_path = self._save_file(filename, file_content, client_id)
            
            # Classify document type
            document_type = self.document_classifier.classify_document(filename, file_path)
            
            # Create document info
            doc_info = DocumentInfo(
                filename=filename,
                file_path=file_path,
                document_type=document_type,
                file_size=len(file_content),
                upload_date=datetime.now(),
                complexity_tier=complexity_tier,
                target_folder=self._determine_target_folder(document_type, complexity_tier)
            )
            
            # Extract data using OCR
            extracted_data = self.ocr_processor.extract_data(file_path, document_type)
            doc_info.extracted_data = extracted_data
            
            # Validate extracted data
            validation_result = self.data_extractor.validate_data(extracted_data, document_type)
            doc_info.validation_status = validation_result['status']
            
            return ProcessingResult(
                success=True,
                document_info=doc_info,
                extracted_data=extracted_data
            )
            
        except Exception as e:
            logger.error(f"Error processing file {filename}: {str(e)}")
            return ProcessingResult(
                success=False,
                document_info=None,
                error_message=str(e)
            )
    
    def _validate_file(self, filename: str, file_content: bytes) -> bool:
        """Validate uploaded file"""
        if not filename or not file_content:
            return False
        
        # Check file extension
        _, ext = os.path.splitext(filename.lower())
        if ext not in self.supported_formats:
            return False
        
        # Check file size (max 10MB)
        if len(file_content) > 10 * 1024 * 1024:
            return False
        
        return True
    
    def _save_file(self, filename: str, file_content: bytes, client_id: str) -> str:
        """Save uploaded file to disk"""
        # Create client-specific directory
        client_dir = os.path.join(self.upload_directory, client_id)
        os.makedirs(client_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}{ext}"
        
        file_path = os.path.join(client_dir, unique_filename)
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return file_path
    
    def _determine_target_folder(self, document_type: str, complexity_tier: str, client_id: str = None, client_name: str = None) -> str:
        """Determine ProConnect folder for document using hierarchical structure"""
        folder_mappings = {
            "W-2": "W-2 Forms",
            "1099-INT": "Investment Income" if complexity_tier in ["Medium", "Hard"] else "W-2 Forms",
            "1099-DIV": "Investment Income" if complexity_tier in ["Medium", "Hard"] else "W-2 Forms",
            "1099-B": "Investment Income",
            "1099-R": "Investment Income" if complexity_tier in ["Medium", "Hard"] else "W-2 Forms",
            "1098-T": "Education Credits",
            "1098-E": "Education Credits",
            "K-1": "Partnership K-1s",
            "Mortgage Statement": "Itemized Deductions" if complexity_tier in ["Medium", "Hard"] else "Standard Deduction",
            "Property Tax": "Itemized Deductions" if complexity_tier in ["Medium", "Hard"] else "Standard Deduction",
            "Charitable Donations": "Itemized Deductions" if complexity_tier in ["Medium", "Hard"] else "Standard Deduction",
            "Rental Statement": "Rental Property",
            "Foreign Bank Statement": "Foreign Assets",
            "FBAR": "Foreign Assets",
            "State Return": "Multi-State Returns" if complexity_tier == "Hard" else "Standard Deduction"
        }
        
        # Get document subfolder
        doc_subfolder = folder_mappings.get(document_type, "Auto-Processed")
        
        # Create client folder name
        client_folder_name = f"{client_id}_{client_name.replace(' ', '_')}" if client_name else f"{client_id}_Client"
        
        # Build hierarchical path: Tier > Client > Document Type
        tier_folder = f"{complexity_tier} Tier Clients"
        return f"{tier_folder}/{client_folder_name}/{doc_subfolder}"
    
    def _organize_in_proconnect(self, client_id: str, complexity_tier: str, 
                              documents: List[DocumentInfo]) -> Dict[str, Any]:
        """Organize documents in ProConnect"""
        if not self.proconnect:
            return {"error": "ProConnect integration not available"}
        
        try:
            # Convert DocumentInfo to upload format
            upload_documents = []
            for doc in documents:
                upload_documents.append({
                    'type': doc.document_type,
                    'file_path': doc.file_path,
                    'filename': doc.filename
                })
            
            # Organize in ProConnect
            result = self.proconnect.organize_client_documents(
                client_id, complexity_tier, upload_documents
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error organizing in ProConnect: {str(e)}")
            return {"error": str(e)}
    
    def _get_folder_structure(self, complexity_tier: str) -> Dict[str, Any]:
        """Get hierarchical folder structure for complexity tier"""
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
        
        return structures.get(complexity_tier, structures["Easy"])

class DocumentClassifier:
    """Advanced document classifier using OCR and AI pattern recognition"""
    
    def __init__(self):
        # Enhanced filename patterns
        self.filename_patterns = {
            'W-2': ['w2', 'w-2', 'wage', 'wage statement'],
            '1099-INT': ['1099-int', '1099int', 'interest', 'bank interest'],
            '1099-DIV': ['1099-div', '1099div', 'dividend', 'stock dividend'],
            '1099-B': ['1099-b', '1099b', 'brokerage', 'stock', 'robinhood', 'schwab', 'fidelity', 'etrade', 'trading'],
            '1099-R': ['1099-r', '1099r', 'retirement', 'pension', '401k', 'ira'],
            '1098-T': ['1098-t', '1098t', 'tuition', 'education', 'college', 'university'],
            '1098-E': ['1098-e', '1098e', 'student loan', 'education loan'],
            'K-1': ['k-1', 'k1', 'partnership', 'llc', 's-corp'],
            'Mortgage Statement': ['mortgage', 'home loan', 'loan statement', 'bank mortgage'],
            'Property Tax': ['property tax', 'real estate tax', 'county tax', 'municipal tax'],
            'Charitable Donations': ['charity', 'donation', 'nonprofit', 'church', 'goodwill'],
            'Rental Statement': ['rental', 'rent', 'lease', 'rental income', 'property management'],
            'Foreign Bank Statement': ['foreign', 'offshore', 'international', 'swiss', 'cayman'],
            'FBAR': ['fbar', 'foreign bank', 'fatca'],
            'State Return': ['state', 'state return', 'state tax'],
            'Business Income': ['schedule c', 'business', 'self-employed', 'contractor', 'freelance'],
            'Investment Summary': ['investment', 'portfolio', 'account statement', 'year-end summary']
        }
        
        # OCR content patterns for smart classification
        self.content_patterns = {
            'W-2': ['wage and tax statement', 'employer identification number', 'wages tips', 'federal income tax withheld'],
            '1099-INT': ['interest income', 'bank interest', 'savings account', 'cd interest'],
            '1099-DIV': ['dividends', 'capital gains', 'ordinary dividends', 'qualified dividends'],
            '1099-B': ['proceeds from broker', 'cost basis', 'wash sale', 'robinhood', 'schwab', 'fidelity'],
            'Mortgage Statement': ['mortgage statement', 'principal and interest', 'escrow', 'loan balance'],
            'Property Tax': ['property tax', 'real estate tax', 'county assessor', 'tax assessment'],
            'Charitable Donations': ['charitable contribution', 'donation receipt', 'tax deductible'],
            'Rental Statement': ['rental income', 'property management', 'rental expenses', 'depreciation'],
            'Business Income': ['schedule c', 'business income', 'self-employment', 'contractor income']
        }
    
    def classify_document(self, filename: str, file_path: str) -> str:
        """Advanced document classification using filename and OCR content"""
        filename_lower = filename.lower()
        
        # First, try filename patterns
        for doc_type, patterns in self.filename_patterns.items():
            for pattern in patterns:
                if pattern in filename_lower:
                    return doc_type
        
        # If filename doesn't match, try OCR content analysis
        try:
            content = self._extract_text_content(file_path)
            if content:
                return self._classify_by_content(content)
        except Exception as e:
            logger.warning(f"Could not extract content from {filename}: {str(e)}")
        
        # Default classification
        return "Unknown Document"
    
    def _extract_text_content(self, file_path: str) -> str:
        """Extract text content from document for classification"""
        try:
            # In a real implementation, you would use:
            # - pytesseract for OCR on images
            # - pdfplumber for PDF text extraction
            # - Pillow for image processing
            
            # For now, simulate content extraction
            import random
            sample_contents = [
                "Wage and Tax Statement 2024",
                "Interest Income from Bank Account",
                "Dividend Income from Investments", 
                "Proceeds from Broker and Barter Transactions",
                "Mortgage Statement - Principal and Interest",
                "Property Tax Assessment Notice",
                "Charitable Contribution Receipt",
                "Rental Income Statement"
            ]
            
            return random.choice(sample_contents)
            
        except Exception as e:
            logger.error(f"Error extracting content: {str(e)}")
            return ""
    
    def _classify_by_content(self, content: str) -> str:
        """Classify document based on extracted content"""
        content_lower = content.lower()
        
        # Score each document type based on content matches
        scores = {}
        for doc_type, patterns in self.content_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern in content_lower:
                    score += 1
            scores[doc_type] = score
        
        # Return the document type with highest score
        if scores:
            best_match = max(scores, key=scores.get)
            if scores[best_match] > 0:
                return best_match
        
        return "Unknown Document"

class OCRProcessor:
    """Handles OCR processing of documents"""
    
    def __init__(self):
        # In a real implementation, you'd use libraries like:
        # - pytesseract for OCR
        # - pdfplumber for PDF text extraction
        # - Pillow for image processing
        pass
    
    def extract_data(self, file_path: str, document_type: str) -> Dict[str, Any]:
        """Extract data from document using OCR"""
        try:
            # Simulate OCR processing
            # In real implementation, this would use actual OCR libraries
            
            extracted_data = {
                'document_type': document_type,
                'extraction_method': 'OCR',
                'extraction_date': datetime.now().isoformat(),
                'confidence_score': 0.85,
                'raw_text': f"Extracted text from {document_type} document",
                'structured_data': self._extract_structured_data(document_type)
            }
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting data from {file_path}: {str(e)}")
            return {
                'document_type': document_type,
                'error': str(e),
                'extraction_method': 'OCR',
                'extraction_date': datetime.now().isoformat()
            }
    
    def _extract_structured_data(self, document_type: str) -> Dict[str, Any]:
        """Extract structured data based on document type"""
        # Simulate structured data extraction
        # In real implementation, this would parse specific fields
        
        if document_type == "W-2":
            return {
                'wages': 50000,
                'federal_withholding': 5000,
                'state_withholding': 2000,
                'social_security_wages': 50000,
                'medicare_wages': 50000
            }
        elif document_type == "1099-INT":
            return {
                'interest_income': 500,
                'payer_name': 'Bank of America',
                'account_number': '****1234'
            }
        elif document_type == "1099-DIV":
            return {
                'dividend_income': 1000,
                'qualified_dividends': 800,
                'payer_name': 'Vanguard'
            }
        else:
            return {
                'document_type': document_type,
                'status': 'processed'
            }

class DataExtractor:
    """Validates and extracts structured data from documents"""
    
    def __init__(self):
        self.validation_rules = {
            'W-2': ['wages', 'federal_withholding'],
            '1099-INT': ['interest_income', 'payer_name'],
            '1099-DIV': ['dividend_income', 'payer_name'],
            '1099-B': ['proceeds', 'cost_basis'],
            '1099-R': ['gross_distribution', 'taxable_amount']
        }
    
    def validate_data(self, extracted_data: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """Validate extracted data"""
        try:
            required_fields = self.validation_rules.get(document_type, [])
            structured_data = extracted_data.get('structured_data', {})
            
            missing_fields = []
            for field in required_fields:
                if field not in structured_data:
                    missing_fields.append(field)
            
            if missing_fields:
                return {
                    'status': 'incomplete',
                    'missing_fields': missing_fields,
                    'confidence': 0.5
                }
            else:
                return {
                    'status': 'complete',
                    'missing_fields': [],
                    'confidence': 0.9
                }
                
        except Exception as e:
            logger.error(f"Error validating data: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'confidence': 0.0
            }

# Example usage
if __name__ == "__main__":
    # Initialize document processor
    processor = DocumentProcessor()
    
    # Example file uploads
    sample_files = [
        {
            'filename': 'W-2_2024.pdf',
            'content': b'fake pdf content'
        },
        {
            'filename': '1099-INT_Bank.pdf', 
            'content': b'fake pdf content'
        }
    ]
    
    # Process files
    result = processor.process_uploaded_files(
        sample_files, 
        client_id="CLIENT_001",
        complexity_tier="Medium"
    )
    
    print("Processing Result:")
    print(json.dumps(result, indent=2, default=str))
