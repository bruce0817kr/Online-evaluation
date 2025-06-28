"""
임시 Stub 구현들 - server.py의 undefined 함수들을 해결하기 위한 파일
"""

import io
from datetime import datetime
from typing import Dict, Any, List
from pydantic import BaseModel, Field
import uuid

# Calculate evaluation scores function
async def calculate_evaluation_scores(sheet_id: str, scores: Dict[str, Any]) -> tuple[float, float]:
    """
    Temporary stub for calculate_evaluation_scores function
    TODO: Implement proper evaluation scoring logic
    """
    try:
        # Simple scoring logic - calculate average
        if not scores:
            return 0.0, 0.0
        
        score_values = []
        for key, value in scores.items():
            if isinstance(value, (int, float)):
                score_values.append(float(value))
            elif isinstance(value, dict) and 'score' in value:
                score_values.append(float(value['score']))
        
        if not score_values:
            return 0.0, 0.0
            
        total_score = sum(score_values)
        weighted_score = total_score / len(score_values)  # Simple average for now
        
        return total_score, weighted_score
    except Exception as e:
        print(f"Error in calculate_evaluation_scores: {e}")
        return 0.0, 0.0

# Notification service
class NotificationServiceStub:
    """
    Temporary stub for notification service
    TODO: Implement proper notification system
    """
    
    async def send_evaluation_complete_notification(self, user_id: str, evaluation_data: Dict[str, Any]):
        """Send evaluation completion notification"""
        print(f"[NOTIFICATION] Evaluation completed for user {user_id}")
        # TODO: Implement actual notification logic
        pass
    
    async def send_project_update_notification(self, project_id: str, notification_data: Dict[str, Any]):
        """Send project update notification"""
        print(f"[NOTIFICATION] Project {project_id} updated: {notification_data.get('title', 'Update')}")
        # TODO: Implement actual notification logic
        pass

# Exporter service
class ExporterStub:
    """
    Temporary stub for export functionality
    TODO: Implement proper export/report generation
    """
    
    def generate_filename(self, base_name: str, file_type: str = "pdf") -> str:
        """Generate filename for export"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}.{file_type}"
    
    async def export_single_evaluation_pdf(self, evaluation_data: Dict[str, Any]) -> io.BytesIO:
        """Export single evaluation as PDF"""
        print(f"[EXPORT] Generating PDF for evaluation")
        # TODO: Implement actual PDF generation
        buffer = io.BytesIO()
        buffer.write(b"PDF content placeholder")
        buffer.seek(0)
        return buffer
    
    async def export_single_evaluation_excel(self, evaluation_data: Dict[str, Any]) -> io.BytesIO:
        """Export single evaluation as Excel"""
        print(f"[EXPORT] Generating Excel for evaluation")
        # TODO: Implement actual Excel generation
        buffer = io.BytesIO()
        buffer.write(b"Excel content placeholder")
        buffer.seek(0)
        return buffer
    
    async def export_bulk_evaluations_excel(self, evaluation_data_list: List[Dict[str, Any]]) -> io.BytesIO:
        """Export multiple evaluations as Excel"""
        print(f"[EXPORT] Generating bulk Excel for {len(evaluation_data_list)} evaluations")
        # TODO: Implement actual bulk Excel generation
        buffer = io.BytesIO()
        buffer.write(b"Bulk Excel content placeholder")
        buffer.seek(0)
        return buffer

# EvaluationItem model
class EvaluationItem(BaseModel):
    """
    Temporary stub for EvaluationItem model
    TODO: Implement proper evaluation item structure
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sheet_id: str
    criterion: str
    score: float
    comment: str = ""
    weight: float = 1.0

# Create service instances
notification_service = NotificationServiceStub()
exporter = ExporterStub()

# Export all needed items
__all__ = [
    'calculate_evaluation_scores',
    'notification_service', 
    'exporter',
    'EvaluationItem',
    'update_project_statistics',
    'background_file_processing'
]

# Additional stub functions found in server.py
async def update_project_statistics(project_id: str):
    """
    Temporary stub for update_project_statistics function
    TODO: Implement proper project statistics update logic
    """
    print(f"[STATS] Updating project statistics for project {project_id}")
    # TODO: Implement actual statistics calculation and update
    pass

async def background_file_processing(file_path: str, file_id: str):
    """
    Temporary stub for background_file_processing function
    TODO: Implement proper background file processing logic
    """
    print(f"[FILE_PROCESSING] Processing file {file_path} with ID {file_id}")
    # TODO: Implement actual file processing (virus scan, metadata extraction, etc.)
    pass
