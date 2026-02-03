"""
Elite Tax & Finance - Document Tracking System
Tracks documents year-over-year and handles N/A scenarios
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

@dataclass
class DocumentHistory:
    """Tracks a document type across multiple years"""
    document_type: str
    years: Dict[str, Dict[str, Any]]  # year -> {status, filename, upload_date, etc.}
    is_required: bool = True
    category: str = "standard"

@dataclass
class ClientDocumentProfile:
    """Complete document profile for a client"""
    client_id: str
    client_name: str
    complexity_tier: str
    document_history: Dict[str, DocumentHistory]
    last_updated: str
    tax_year: int

class DocumentTracker:
    """Manages year-over-year document tracking"""
    
    def __init__(self, data_directory: str = "client_documents"):
        self.data_directory = data_directory
        os.makedirs(data_directory, exist_ok=True)
        
        # Define standard document types for each complexity tier
        self.standard_documents = {
            "Easy": [
                "W-2", "1099-INT", "1099-DIV", "1099-R", "1098-T", 
                "Property Tax", "Charitable Donations"
            ],
            "Medium": [
                "W-2", "1099-INT", "1099-DIV", "1099-B", "1099-R", 
                "1098-T", "1098-E", "Mortgage Statement", "Property Tax", 
                "Charitable Donations", "Investment Summary"
            ],
            "Hard": [
                "W-2", "1099-INT", "1099-DIV", "1099-B", "1099-R", 
                "1098-T", "1098-E", "K-1", "Mortgage Statement", 
                "Property Tax", "Charitable Donations", "Rental Statement",
                "Foreign Bank Statement", "FBAR", "Business Income", 
                "Investment Summary", "State Return"
            ]
        }
    
    def get_client_profile(self, client_id: str) -> Optional[ClientDocumentProfile]:
        """Get client's document profile"""
        try:
            file_path = os.path.join(self.data_directory, f"{client_id}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    return self._dict_to_profile(data)
            return None
        except Exception as e:
            print(f"Error loading client profile: {e}")
            return None
    
    def create_client_profile(self, client_id: str, client_name: str, 
                            complexity_tier: str, tax_year: int) -> ClientDocumentProfile:
        """Create new client document profile"""
        document_history = {}
        
        # Initialize with standard documents for the complexity tier
        for doc_type in self.standard_documents.get(complexity_tier, []):
            document_history[doc_type] = DocumentHistory(
                document_type=doc_type,
                years={},
                is_required=True,
                category="standard"
            )
        
        profile = ClientDocumentProfile(
            client_id=client_id,
            client_name=client_name,
            complexity_tier=complexity_tier,
            document_history=document_history,
            last_updated=datetime.now().isoformat(),
            tax_year=tax_year
        )
        
        self.save_client_profile(profile)
        return profile
    
    def save_client_profile(self, profile: ClientDocumentProfile):
        """Save client profile to disk"""
        try:
            file_path = os.path.join(self.data_directory, f"{profile.client_id}.json")
            with open(file_path, 'w') as f:
                json.dump(asdict(profile), f, indent=2)
        except Exception as e:
            print(f"Error saving client profile: {e}")
    
    def add_document(self, client_id: str, document_type: str, 
                    filename: str, tax_year: int) -> bool:
        """Add a document to client's history"""
        try:
            profile = self.get_client_profile(client_id)
            if not profile:
                return False
            
            # Ensure document type exists in history
            if document_type not in profile.document_history:
                profile.document_history[document_type] = DocumentHistory(
                    document_type=document_type,
                    years={},
                    is_required=False,
                    category="custom"
                )
            
            # Add document to year
            year_str = str(tax_year)
            profile.document_history[document_type].years[year_str] = {
                "status": "uploaded",
                "filename": filename,
                "upload_date": datetime.now().isoformat(),
                "processed": True
            }
            
            profile.last_updated = datetime.now().isoformat()
            self.save_client_profile(profile)
            return True
            
        except Exception as e:
            print(f"Error adding document: {e}")
            return False
    
    def mark_document_na(self, client_id: str, document_type: str, 
                        tax_year: int, reason: str = "Not applicable") -> bool:
        """Mark a document as N/A for a specific year"""
        try:
            profile = self.get_client_profile(client_id)
            if not profile:
                return False
            
            # Ensure document type exists
            if document_type not in profile.document_history:
                profile.document_history[document_type] = DocumentHistory(
                    document_type=document_type,
                    years={},
                    is_required=False,
                    category="custom"
                )
            
            # Mark as N/A
            year_str = str(tax_year)
            profile.document_history[document_type].years[year_str] = {
                "status": "na",
                "reason": reason,
                "date_marked": datetime.now().isoformat(),
                "processed": True
            }
            
            profile.last_updated = datetime.now().isoformat()
            self.save_client_profile(profile)
            return True
            
        except Exception as e:
            print(f"Error marking document N/A: {e}")
            return False
    
    def get_required_documents(self, client_id: str, tax_year: int) -> Dict[str, Any]:
        """Get list of required documents for a client for a specific year"""
        try:
            profile = self.get_client_profile(client_id)
            if not profile:
                return {"error": "Client profile not found"}
            
            required_docs = {}
            
            for doc_type, history in profile.document_history.items():
                year_str = str(tax_year)
                
                # Check if document exists for this year
                if year_str in history.years:
                    doc_status = history.years[year_str]
                    required_docs[doc_type] = {
                        "status": doc_status["status"],
                        "required": history.is_required,
                        "category": history.category,
                        "year_data": doc_status
                    }
                else:
                    # Document not provided for this year
                    required_docs[doc_type] = {
                        "status": "missing",
                        "required": history.is_required,
                        "category": history.category,
                        "year_data": None
                    }
            
            return {
                "client_id": client_id,
                "tax_year": tax_year,
                "complexity_tier": profile.complexity_tier,
                "documents": required_docs,
                "summary": self._generate_summary(required_docs)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _generate_summary(self, documents: Dict[str, Any]) -> Dict[str, int]:
        """Generate summary of document status"""
        summary = {
            "uploaded": 0,
            "na": 0,
            "missing": 0,
            "total_required": 0
        }
        
        for doc_type, doc_info in documents.items():
            if doc_info["required"]:
                summary["total_required"] += 1
                
            status = doc_info["status"]
            if status == "uploaded":
                summary["uploaded"] += 1
            elif status == "na":
                summary["na"] += 1
            elif status == "missing":
                summary["missing"] += 1
        
        return summary
    
    def _dict_to_profile(self, data: Dict[str, Any]) -> ClientDocumentProfile:
        """Convert dictionary to ClientDocumentProfile"""
        document_history = {}
        for doc_type, doc_data in data["document_history"].items():
            document_history[doc_type] = DocumentHistory(**doc_data)
        
        return ClientDocumentProfile(
            client_id=data["client_id"],
            client_name=data["client_name"],
            complexity_tier=data["complexity_tier"],
            document_history=document_history,
            last_updated=data["last_updated"],
            tax_year=data["tax_year"]
        )
    
    def get_document_suggestions(self, client_id: str, tax_year: int) -> List[str]:
        """Get smart suggestions for documents based on previous years"""
        try:
            profile = self.get_client_profile(client_id)
            if not profile:
                return []
            
            suggestions = []
            
            # Look at previous year's documents
            prev_year = str(tax_year - 1)
            
            for doc_type, history in profile.document_history.items():
                if prev_year in history.years:
                    prev_status = history.years[prev_year]["status"]
                    
                    if prev_status == "uploaded":
                        # Client had this document last year, suggest it for this year
                        suggestions.append(f"Consider uploading {doc_type} (you had this last year)")
                    elif prev_status == "na":
                        # Client marked this as N/A last year, ask if still N/A
                        suggestions.append(f"Is {doc_type} still not applicable this year?")
            
            return suggestions
            
        except Exception as e:
            print(f"Error generating suggestions: {e}")
            return []

# Example usage
if __name__ == "__main__":
    tracker = DocumentTracker()
    
    # Create a client profile
    profile = tracker.create_client_profile(
        "CLIENT_001", "John Smith", "Medium", 2024
    )
    
    # Add some documents
    tracker.add_document("CLIENT_001", "W-2", "W-2_2024.pdf", 2024)
    tracker.add_document("CLIENT_001", "1099-INT", "Bank_Interest_2024.pdf", 2024)
    tracker.mark_document_na("CLIENT_001", "Rental Statement", 2024, "Sold rental property")
    
    # Get required documents
    required = tracker.get_required_documents("CLIENT_001", 2024)
    print("Required Documents:")
    print(json.dumps(required, indent=2))
    
    # Get suggestions for next year
    suggestions = tracker.get_document_suggestions("CLIENT_001", 2025)
    print("\nSuggestions for 2025:")
    for suggestion in suggestions:
        print(f"- {suggestion}")

