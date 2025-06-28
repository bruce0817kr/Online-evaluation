"""
Enhanced Evaluation Export API Endpoints
Advanced formatting, templates, personas, and export options for evaluation reports
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import logging
import io
import json
import uuid
import os
from pydantic import BaseModel, Field

from models import User
from security import get_current_user, check_admin_or_secretary, db
from evaluation_print_endpoints import (
    get_evaluation_data, 
    create_individual_evaluation_pdf,
    print_jobs,
    PrintJobStatus
)

logger = logging.getLogger(__name__)

# Enhanced Export Router
enhanced_export_router = APIRouter(prefix="/api/evaluations/enhanced-export", tags=["Enhanced Export"])

# Enhanced Export Enums
class ExportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "excel" 
    WORD = "word"
    POWERPOINT = "powerpoint"
    HTML = "html"

class ExportTemplate(str, Enum):
    STANDARD = "standard"
    GOVERNMENT = "government"
    CORPORATE = "corporate"
    ACADEMIC = "academic"
    TECHNICAL = "technical"
    MINIMAL = "minimal"
    DETAILED = "detailed"

class ColorScheme(str, Enum):
    PROFESSIONAL = "professional"
    GOVERNMENT = "government"
    CORPORATE = "corporate"
    ACADEMIC = "academic"
    MODERN = "modern"
    CLASSIC = "classic"

class ExportPersona(str, Enum):
    GOVERNMENT_AUDITOR = "government_auditor"
    CORPORATE_EXECUTIVE = "corporate_executive"  
    ACADEMIC_REVIEWER = "academic_reviewer"
    TECHNICAL_ASSESSOR = "technical_assessor"

# Enhanced Export Models
class StyleOptions(BaseModel):
    """Advanced styling options for exports"""
    font_family: str = Field("Noto Sans KR", description="Font family for the document")
    font_size: int = Field(10, ge=8, le=16, description="Base font size")
    color_scheme: ColorScheme = Field(ColorScheme.PROFESSIONAL, description="Color scheme")
    include_logo: bool = Field(True, description="Include organization logo")
    watermark: Optional[str] = Field(None, description="Watermark text")
    header_style: str = Field("modern", description="Header style: modern, classic, minimal")
    table_style: str = Field("striped", description="Table style: striped, bordered, minimal")

class MetadataOptions(BaseModel):
    """Metadata and security options"""
    include_timestamps: bool = Field(True, description="Include creation/submission timestamps")
    include_evaluator_info: bool = Field(True, description="Include evaluator information")
    include_qr_code: bool = Field(False, description="Include QR code for verification")
    digital_signature: bool = Field(False, description="Add digital signature")
    confidentiality_level: str = Field("internal", description="Confidentiality level")
    document_classification: Optional[str] = Field(None, description="Document classification")

class ContentOptions(BaseModel):
    """Content inclusion options"""
    include_sections: List[str] = Field(
        default=["summary", "details", "scores", "comments", "signatures"],
        description="Sections to include"
    )
    include_charts: bool = Field(True, description="Include score visualization charts")
    include_comparison: bool = Field(False, description="Include comparison with other evaluations")
    include_recommendations: bool = Field(True, description="Include AI-generated recommendations")
    include_appendices: bool = Field(False, description="Include detailed appendices")
    summary_length: str = Field("medium", description="Summary length: short, medium, long")

class EnhancedExportOptions(BaseModel):
    """Comprehensive export configuration"""
    format: ExportFormat = Field(ExportFormat.PDF, description="Export format")
    template: ExportTemplate = Field(ExportTemplate.STANDARD, description="Document template")
    persona: Optional[ExportPersona] = Field(None, description="Target persona for optimization")
    style_options: StyleOptions = Field(default_factory=StyleOptions)
    metadata_options: MetadataOptions = Field(default_factory=MetadataOptions)
    content_options: ContentOptions = Field(default_factory=ContentOptions)
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom fields")
    
class ExportPreview(BaseModel):
    """Export preview information"""
    preview_url: str
    thumbnail_url: str
    page_count: int
    estimated_file_size: int
    estimated_generation_time: float
    template_info: Dict[str, Any]
    
class ExportResult(BaseModel):
    """Export operation result"""
    success: bool
    file_url: Optional[str]
    file_size: Optional[int]
    generation_time: float
    format: str
    template_used: str
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class TemplateInfo(BaseModel):
    """Template information"""
    id: str
    name: str
    description: str
    preview_url: str
    supported_formats: List[ExportFormat]
    customizable_elements: List[str]
    is_default: bool
    persona_optimized: List[ExportPersona]
    tags: List[str]

# Enhanced Export Service
class EnhancedExportService:
    """Advanced export service with template and persona support"""
    
    def __init__(self):
        self.templates = self._load_templates()
        self.persona_defaults = self._load_persona_defaults()
    
    def _load_templates(self) -> Dict[str, Dict]:
        """Load available export templates"""
        return {
            "standard": {
                "name": "표준 평가서",
                "description": "일반적인 평가 보고서 형식",
                "sections": ["header", "summary", "details", "scores", "comments", "footer"],
                "styling": {"layout": "two-column", "font": "professional"},
                "preview_features": ["깔끔한 레이아웃", "표준 색상", "기본 차트"]
            },
            "government": {
                "name": "정부기관 양식",
                "description": "정부기관 표준 보고서 형식",
                "sections": ["official_header", "classification", "summary", "detailed_analysis", "recommendations", "approvals"],
                "styling": {"layout": "formal", "watermark": "OFFICIAL", "seal": True},
                "preview_features": ["공식 문서 형식", "워터마크", "디지털 서명"]
            },
            "corporate": {
                "name": "기업 임원 보고서",
                "description": "기업 임원진을 위한 요약 중심 보고서",
                "sections": ["executive_summary", "key_metrics", "recommendations", "appendix"],
                "styling": {"layout": "dashboard", "charts": True, "infographics": True},
                "preview_features": ["임원진 요약", "인포그래픽", "대시보드 스타일"]
            },
            "academic": {
                "name": "학술 평가서",
                "description": "학술기관용 상세 분석 보고서",
                "sections": ["abstract", "methodology", "detailed_analysis", "statistical_summary", "bibliography"],
                "styling": {"layout": "academic", "citations": True, "detailed_tables": True},
                "preview_features": ["학술 형식", "상세 분석", "통계 요약"]
            },
            "technical": {
                "name": "기술 평가서",
                "description": "기술적 상세사항 중심 보고서",
                "sections": ["technical_summary", "criteria_analysis", "scoring_matrix", "technical_recommendations"],
                "styling": {"layout": "technical", "code_blocks": True, "diagrams": True},
                "preview_features": ["기술 중심", "상세 기준", "매트릭스 분석"]
            }
        }
    
    def _load_persona_defaults(self) -> Dict[str, EnhancedExportOptions]:
        """Load persona-based default configurations"""
        return {
            "government_auditor": EnhancedExportOptions(
                template=ExportTemplate.GOVERNMENT,
                style_options=StyleOptions(
                    color_scheme=ColorScheme.GOVERNMENT,
                    watermark="OFFICIAL",
                    font_family="Noto Sans KR",
                    header_style="formal"
                ),
                metadata_options=MetadataOptions(
                    digital_signature=True,
                    confidentiality_level="government",
                    document_classification="공개",
                    include_qr_code=True
                ),
                content_options=ContentOptions(
                    include_sections=["summary", "details", "scores", "compliance", "signatures"],
                    include_comparison=False,
                    summary_length="long",
                    include_appendices=True
                )
            ),
            "corporate_executive": EnhancedExportOptions(
                template=ExportTemplate.CORPORATE,
                style_options=StyleOptions(
                    color_scheme=ColorScheme.CORPORATE,
                    font_family="Noto Sans KR",
                    header_style="modern"
                ),
                content_options=ContentOptions(
                    include_sections=["executive_summary", "key_findings", "recommendations"],
                    include_charts=True,
                    summary_length="short",
                    include_comparison=True
                )
            ),
            "academic_reviewer": EnhancedExportOptions(
                template=ExportTemplate.ACADEMIC,
                style_options=StyleOptions(
                    color_scheme=ColorScheme.ACADEMIC,
                    font_family="Noto Serif KR",
                    header_style="classic"
                ),
                content_options=ContentOptions(
                    include_sections=["abstract", "methodology", "detailed_analysis", "bibliography"],
                    include_appendices=True,
                    summary_length="long",
                    include_charts=True
                )
            ),
            "technical_assessor": EnhancedExportOptions(
                template=ExportTemplate.TECHNICAL,
                style_options=StyleOptions(
                    color_scheme=ColorScheme.MODERN,
                    font_family="Noto Sans KR",
                    header_style="minimal"
                ),
                content_options=ContentOptions(
                    include_sections=["technical_summary", "criteria_analysis", "scoring_matrix"],
                    include_charts=True,
                    summary_length="medium",
                    include_appendices=False
                )
            )
        }
    
    async def apply_persona_defaults(
        self, 
        options: EnhancedExportOptions, 
        persona: ExportPersona
    ) -> EnhancedExportOptions:
        """Apply persona-based defaults to export options"""
        if persona.value in self.persona_defaults:
            default_options = self.persona_defaults[persona.value]
            
            # Create a new options object with persona defaults applied
            merged_options = EnhancedExportOptions(
                format=options.format,
                template=default_options.template if options.template == ExportTemplate.STANDARD else options.template,
                persona=persona,
                style_options=default_options.style_options if not options.style_options else options.style_options,
                metadata_options=default_options.metadata_options if not options.metadata_options else options.metadata_options,
                content_options=default_options.content_options if not options.content_options else options.content_options,
                custom_fields=options.custom_fields
            )
                
            return merged_options
        
        return options
    
    async def generate_preview(
        self, 
        evaluation_id: str, 
        options: EnhancedExportOptions
    ) -> ExportPreview:
        """Generate export preview information"""
        
        # Get template information
        template_info = self.templates.get(options.template.value, {})
        
        # Estimate document properties
        estimated_pages = 5  # Base pages
        if options.content_options.include_appendices:
            estimated_pages += 3
        if options.content_options.include_charts:
            estimated_pages += 2
        if options.content_options.include_comparison:
            estimated_pages += 1
        if options.content_options.summary_length == "long":
            estimated_pages += 1
            
        estimated_size = estimated_pages * 150 * 1024  # ~150KB per page
        estimated_time = estimated_pages * 0.5  # 0.5 seconds per page
        
        # Add template-specific adjustments
        if options.template == ExportTemplate.GOVERNMENT:
            estimated_time += 1.0  # Additional time for official formatting
        elif options.template == ExportTemplate.CORPORATE:
            estimated_size += 200 * 1024  # Additional size for charts
        
        return ExportPreview(
            preview_url=f"/api/files/preview/{evaluation_id}",
            thumbnail_url=f"/api/files/thumbnail/{evaluation_id}",
            page_count=estimated_pages,
            estimated_file_size=estimated_size,
            estimated_generation_time=estimated_time,
            template_info={
                **template_info,
                "persona_optimized": options.persona.value if options.persona else None,
                "style_preview": {
                    "color_scheme": options.style_options.color_scheme.value,
                    "font_family": options.style_options.font_family,
                    "watermark": options.style_options.watermark
                }
            }
        )
    
    async def validate_export_options(self, options: EnhancedExportOptions) -> Dict[str, List[str]]:
        """Validate export options and return errors/warnings"""
        errors = []
        warnings = []
        
        # Check template compatibility with format
        template_formats = {
            ExportTemplate.GOVERNMENT: [ExportFormat.PDF, ExportFormat.WORD],
            ExportTemplate.CORPORATE: [ExportFormat.PDF, ExportFormat.EXCEL, ExportFormat.POWERPOINT],
            ExportTemplate.ACADEMIC: [ExportFormat.PDF, ExportFormat.WORD],
            ExportTemplate.TECHNICAL: [ExportFormat.PDF, ExportFormat.HTML]
        }
        
        if options.template in template_formats:
            if options.format not in template_formats[options.template]:
                warnings.append(f"{options.template.value} 템플릿은 {options.format.value} 형식을 완전히 지원하지 않을 수 있습니다.")
        
        # Validate content sections
        valid_sections = [
            "summary", "details", "scores", "comments", "signatures", 
            "charts", "appendices", "executive_summary", "key_findings",
            "recommendations", "abstract", "methodology", "detailed_analysis",
            "statistical_summary", "bibliography", "technical_summary",
            "criteria_analysis", "scoring_matrix", "compliance"
        ]
        
        for section in options.content_options.include_sections:
            if section not in valid_sections:
                warnings.append(f"알 수 없는 섹션: {section}")
        
        # Check persona-template compatibility
        persona_templates = {
            ExportPersona.GOVERNMENT_AUDITOR: [ExportTemplate.GOVERNMENT, ExportTemplate.STANDARD],
            ExportPersona.CORPORATE_EXECUTIVE: [ExportTemplate.CORPORATE, ExportTemplate.STANDARD],
            ExportPersona.ACADEMIC_REVIEWER: [ExportTemplate.ACADEMIC, ExportTemplate.STANDARD],
            ExportPersona.TECHNICAL_ASSESSOR: [ExportTemplate.TECHNICAL, ExportTemplate.STANDARD]
        }
        
        if options.persona and options.template not in persona_templates.get(options.persona, []):
            warnings.append(f"{options.persona.value} 페르소나는 {options.template.value} 템플릿과 최적화되지 않았습니다.")
        
        return {"errors": errors, "warnings": warnings}

# Initialize enhanced service
enhanced_export_service = EnhancedExportService()

# Enhanced Export API Endpoints

@enhanced_export_router.get("/templates")
async def get_export_templates(
    template_type: Optional[str] = Query(None, description="Filter by template type"),
    format_filter: Optional[ExportFormat] = Query(None, description="Filter by supported format"),
    current_user: User = Depends(get_current_user)
) -> List[TemplateInfo]:
    """Get available export templates with enhanced information"""
    
    templates = []
    for template_id, template_data in enhanced_export_service.templates.items():
        
        # Filter by type if specified
        if template_type and template_type not in template_data.get("tags", []):
            continue
        
        # Determine supported formats based on template
        supported_formats = [ExportFormat.PDF, ExportFormat.EXCEL]
        if template_id in ["government", "academic"]:
            supported_formats.append(ExportFormat.WORD)
        if template_id == "corporate":
            supported_formats.append(ExportFormat.POWERPOINT)
        if template_id == "technical":
            supported_formats.append(ExportFormat.HTML)
        
        # Filter by format if specified
        if format_filter and format_filter not in supported_formats:
            continue
        
        # Determine persona optimization
        persona_optimized = []
        if template_id == "government":
            persona_optimized = [ExportPersona.GOVERNMENT_AUDITOR]
        elif template_id == "corporate":
            persona_optimized = [ExportPersona.CORPORATE_EXECUTIVE]
        elif template_id == "academic":
            persona_optimized = [ExportPersona.ACADEMIC_REVIEWER]
        elif template_id == "technical":
            persona_optimized = [ExportPersona.TECHNICAL_ASSESSOR]
        
        template_info = TemplateInfo(
            id=template_id,
            name=template_data["name"],
            description=template_data["description"],
            preview_url=f"/api/evaluations/enhanced-export/templates/{template_id}/preview",
            supported_formats=supported_formats,
            customizable_elements=["styling", "sections", "metadata", "content"],
            is_default=(template_id == "standard"),
            persona_optimized=persona_optimized,
            tags=template_data.get("preview_features", ["standard"])
        )
        templates.append(template_info)
    
    return templates

@enhanced_export_router.get("/templates/{template_id}/preview")
async def get_template_preview(
    template_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed template preview information"""
    
    if template_id not in enhanced_export_service.templates:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다")
    
    template_data = enhanced_export_service.templates[template_id]
    
    return {
        "template_id": template_id,
        "template_info": template_data,
        "sample_sections": template_data["sections"],
        "styling_options": template_data["styling"],
        "preview_features": template_data.get("preview_features", []),
        "recommended_personas": [
            persona.value for persona, options in enhanced_export_service.persona_defaults.items()
            if options.template.value == template_id
        ]
    }

@enhanced_export_router.get("/personas")
async def get_export_personas(
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get available export personas with their characteristics"""
    
    personas = []
    for persona_key, persona_options in enhanced_export_service.persona_defaults.items():
        persona_info = {
            "id": persona_key,
            "name": persona_key.replace("_", " ").title(),
            "description": f"{persona_key.replace('_', ' ').title()}를 위한 최적화된 설정",
            "template": persona_options.template.value,
            "color_scheme": persona_options.style_options.color_scheme.value,
            "key_features": [],
            "recommended_sections": persona_options.content_options.include_sections,
            "summary_length": persona_options.content_options.summary_length
        }
        
        # Add persona-specific features
        if persona_key == "government_auditor":
            persona_info["key_features"] = ["공식 문서 형식", "디지털 서명", "워터마크", "QR 코드"]
        elif persona_key == "corporate_executive":
            persona_info["key_features"] = ["요약 중심", "차트 포함", "비교 분석", "대시보드"]
        elif persona_key == "academic_reviewer":
            persona_info["key_features"] = ["학술 형식", "상세 분석", "부록 포함", "참고문헌"]
        elif persona_key == "technical_assessor":
            persona_info["key_features"] = ["기술 중심", "매트릭스 분석", "최신 디자인"]
        
        personas.append(persona_info)
    
    return personas

@enhanced_export_router.get("/personas/{persona}/defaults")
async def get_persona_defaults(
    persona: ExportPersona,
    current_user: User = Depends(get_current_user)
) -> EnhancedExportOptions:
    """Get default export options for a specific persona"""
    
    if persona.value in enhanced_export_service.persona_defaults:
        return enhanced_export_service.persona_defaults[persona.value]
    
    # Return standard defaults if persona not found
    return EnhancedExportOptions()

@enhanced_export_router.post("/preview/{evaluation_id}")
async def preview_enhanced_export(
    evaluation_id: str,
    options: EnhancedExportOptions,
    current_user: User = Depends(get_current_user)
) -> ExportPreview:
    """Generate enhanced export preview with validation"""
    
    try:
        # Validate options first
        validation_result = await enhanced_export_service.validate_export_options(options)
        if validation_result["errors"]:
            raise HTTPException(
                status_code=400,
                detail=f"Export 옵션 오류: {', '.join(validation_result['errors'])}"
            )
        
        # Apply persona defaults if specified
        if options.persona:
            options = await enhanced_export_service.apply_persona_defaults(options, options.persona)
        
        preview = await enhanced_export_service.generate_preview(evaluation_id, options)
        
        # Add validation warnings to preview
        if validation_result["warnings"]:
            preview.template_info["warnings"] = validation_result["warnings"]
        
        return preview
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced preview generation failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"고급 미리보기 생성 중 오류가 발생했습니다: {str(e)}"
        )

@enhanced_export_router.post("/export/{evaluation_id}")
async def export_enhanced_evaluation(
    evaluation_id: str,
    options: EnhancedExportOptions,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Export evaluation with enhanced formatting options"""
    
    try:
        # Validate options
        validation_result = await enhanced_export_service.validate_export_options(options)
        if validation_result["errors"]:
            raise HTTPException(
                status_code=400,
                detail=f"Export 옵션 오류: {', '.join(validation_result['errors'])}"
            )
        
        # Apply persona defaults if specified
        if options.persona:
            options = await enhanced_export_service.apply_persona_defaults(options, options.persona)
        
        # Create enhanced export job
        job_id = str(uuid.uuid4())
        
        # Initialize job status
        print_jobs[job_id] = PrintJobStatus(
            job_id=job_id,
            status="pending",
            created_at=datetime.utcnow()
        ).dict()
        
        # Add enhanced metadata to job
        print_jobs[job_id].update({
            "template_used": options.template.value,
            "persona_used": options.persona.value if options.persona else None,
            "format_used": options.format.value,
            "validation_warnings": validation_result.get("warnings", [])
        })
        
        # Start background task with enhanced processing
        background_tasks.add_task(
            process_enhanced_export_job,
            job_id,
            evaluation_id,
            options.dict(),
            current_user
        )
        
        logger.info(f"Enhanced export job created: {job_id}", extra={
            'user_id': current_user.id,
            'evaluation_id': evaluation_id,
            'template': options.template.value,
            'persona': options.persona.value if options.persona else None,
            'format': options.format.value
        })
        
        return {
            "success": True,
            "job_id": job_id,
            "message": "고급 출력 작업이 시작되었습니다",
            "template": options.template.value,
            "format": options.format.value,
            "persona": options.persona.value if options.persona else None,
            "warnings": validation_result.get("warnings", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced export failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"고급 Export 생성 중 오류가 발생했습니다: {str(e)}"
        )

@enhanced_export_router.post("/bulk-export")
async def bulk_enhanced_export(
    evaluation_ids: List[str],
    options: EnhancedExportOptions,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(check_admin_or_secretary)
) -> Dict[str, Any]:
    """Bulk export multiple evaluations with enhanced formatting"""
    
    try:
        # Validate options
        validation_result = await enhanced_export_service.validate_export_options(options)
        if validation_result["errors"]:
            raise HTTPException(
                status_code=400,
                detail=f"Export 옵션 오류: {', '.join(validation_result['errors'])}"
            )
        
        # Apply persona defaults if specified
        if options.persona:
            options = await enhanced_export_service.apply_persona_defaults(options, options.persona)
        
        # Create bulk export job
        job_id = str(uuid.uuid4())
        
        # Initialize job status
        print_jobs[job_id] = PrintJobStatus(
            job_id=job_id,
            status="pending",
            created_at=datetime.utcnow()
        ).dict()
        
        # Add bulk export metadata
        print_jobs[job_id].update({
            "export_type": "bulk_enhanced",
            "total_evaluations": len(evaluation_ids),
            "template_used": options.template.value,
            "persona_used": options.persona.value if options.persona else None,
            "format_used": options.format.value
        })
        
        # Start background task
        background_tasks.add_task(
            process_bulk_enhanced_export_job,
            job_id,
            evaluation_ids,
            options.dict(),
            current_user
        )
        
        logger.info(f"Bulk enhanced export job created: {job_id}", extra={
            'user_id': current_user.id,
            'evaluation_count': len(evaluation_ids),
            'template': options.template.value,
            'persona': options.persona.value if options.persona else None
        })
        
        return {
            "success": True,
            "job_id": job_id,
            "message": f"{len(evaluation_ids)}개 평가의 고급 일괄 출력이 시작되었습니다",
            "total_evaluations": len(evaluation_ids),
            "template": options.template.value,
            "warnings": validation_result.get("warnings", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk enhanced export failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"일괄 고급 Export 생성 중 오류가 발생했습니다: {str(e)}"
        )

# Enhanced Background Processing Functions

async def process_enhanced_export_job(
    job_id: str, 
    evaluation_id: str, 
    options: Dict[str, Any], 
    user: User
):
    """Process enhanced export job with advanced formatting"""
    
    try:
        print_jobs[job_id]["status"] = "processing"
        print_jobs[job_id]["progress"] = 10
        
        # Get evaluation data
        evaluation_data = await get_evaluation_data(evaluation_id)
        print_jobs[job_id]["progress"] = 30
        
        # Enhance data with options
        enhanced_data = await enhance_evaluation_data_with_options(evaluation_data, options)
        print_jobs[job_id]["progress"] = 60
        
        # Generate enhanced export
        export_content = await generate_enhanced_export(enhanced_data, options)
        print_jobs[job_id]["progress"] = 90
        
        # Save file
        template_name = options.get("template", "standard")
        persona_name = options.get("persona", "default")
        format_type = options.get("format", "pdf")
        
        filename = f"enhanced_{evaluation_id}_{template_name}_{persona_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
        file_path = f"outputs/{filename}"
        
        os.makedirs("outputs", exist_ok=True)
        
        if isinstance(export_content, bytes):
            with open(file_path, "wb") as f:
                f.write(export_content)
        else:
            # For string content (HTML, etc.)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(export_content)
        
        # Complete job
        print_jobs[job_id]["status"] = "completed"
        print_jobs[job_id]["progress"] = 100
        print_jobs[job_id]["file_path"] = file_path
        print_jobs[job_id]["completed_at"] = datetime.utcnow()
        
        logger.info(f"Enhanced export job completed: {job_id}")
        
    except Exception as e:
        print_jobs[job_id]["status"] = "failed"
        print_jobs[job_id]["error_message"] = str(e)
        logger.error(f"Enhanced export job failed: {job_id}, error: {e}")

async def process_bulk_enhanced_export_job(
    job_id: str,
    evaluation_ids: List[str],
    options: Dict[str, Any],
    user: User
):
    """Process bulk enhanced export job"""
    
    try:
        import zipfile
        
        print_jobs[job_id]["status"] = "processing"
        print_jobs[job_id]["progress"] = 5
        
        template_name = options.get("template", "standard")
        persona_name = options.get("persona", "default")
        format_type = options.get("format", "pdf")
        
        zip_filename = f"bulk_enhanced_{template_name}_{persona_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        file_path = f"outputs/{zip_filename}"
        
        os.makedirs("outputs", exist_ok=True)
        
        with zipfile.ZipFile(file_path, 'w') as zipf:
            total_evaluations = len(evaluation_ids)
            
            for i, evaluation_id in enumerate(evaluation_ids):
                try:
                    # Get and enhance evaluation data
                    evaluation_data = await get_evaluation_data(evaluation_id)
                    enhanced_data = await enhance_evaluation_data_with_options(evaluation_data, options)
                    
                    # Generate export content
                    export_content = await generate_enhanced_export(enhanced_data, options)
                    
                    # Create filename for this evaluation
                    company_name = enhanced_data.get("company", {}).get("name", "unknown")
                    safe_company_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).strip()
                    
                    eval_filename = f"{safe_company_name}_{template_name}_{evaluation_id}.{format_type}"
                    
                    # Add to zip
                    zipf.writestr(eval_filename, export_content)
                    
                    # Update progress
                    progress = 10 + int((i + 1) / total_evaluations * 80)
                    print_jobs[job_id]["progress"] = progress
                    
                except Exception as e:
                    logger.error(f"Failed to process evaluation {evaluation_id} in bulk export: {e}")
                    # Continue with other evaluations
                    continue
        
        # Complete job
        print_jobs[job_id]["status"] = "completed"
        print_jobs[job_id]["progress"] = 100
        print_jobs[job_id]["file_path"] = file_path
        print_jobs[job_id]["completed_at"] = datetime.utcnow()
        
        logger.info(f"Bulk enhanced export job completed: {job_id}")
        
    except Exception as e:
        print_jobs[job_id]["status"] = "failed"
        print_jobs[job_id]["error_message"] = str(e)
        logger.error(f"Bulk enhanced export job failed: {job_id}, error: {e}")

async def enhance_evaluation_data_with_options(data: Dict, options: Dict) -> Dict:
    """Enhance evaluation data based on export options"""
    
    enhanced = data.copy()
    
    # Add export metadata
    enhanced["export_metadata"] = {
        "generated_at": datetime.utcnow(),
        "template": options.get("template", "standard"),
        "format": options.get("format", "pdf"),
        "persona": options.get("persona"),
        "confidentiality": options.get("metadata_options", {}).get("confidentiality_level", "internal"),
        "document_classification": options.get("metadata_options", {}).get("document_classification"),
        "include_qr_code": options.get("metadata_options", {}).get("include_qr_code", False),
        "digital_signature": options.get("metadata_options", {}).get("digital_signature", False)
    }
    
    # Add styling information
    style_options = options.get("style_options", {})
    enhanced["styling"] = {
        "font_family": style_options.get("font_family", "Noto Sans KR"),
        "font_size": style_options.get("font_size", 10),
        "color_scheme": style_options.get("color_scheme", "professional"),
        "watermark": style_options.get("watermark"),
        "header_style": style_options.get("header_style", "modern"),
        "table_style": style_options.get("table_style", "striped"),
        "include_logo": style_options.get("include_logo", True)
    }
    
    # Add content configuration
    content_options = options.get("content_options", {})
    enhanced["content_config"] = {
        "include_sections": content_options.get("include_sections", ["summary", "details", "scores"]),
        "include_charts": content_options.get("include_charts", True),
        "include_comparison": content_options.get("include_comparison", False),
        "include_recommendations": content_options.get("include_recommendations", True),
        "include_appendices": content_options.get("include_appendices", False),
        "summary_length": content_options.get("summary_length", "medium")
    }
    
    return enhanced

async def generate_enhanced_export(data: Dict, options: Dict) -> bytes:
    """Generate enhanced export based on format and template"""
    
    format_type = options.get("format", "pdf")
    template = options.get("template", "standard")
    
    if format_type == "pdf":
        return await generate_enhanced_pdf(data, options)
    elif format_type == "excel":
        return await generate_enhanced_excel(data, options)
    elif format_type == "word":
        return await generate_enhanced_word(data, options)
    elif format_type == "html":
        return await generate_enhanced_html(data, options)
    else:
        # Fallback to standard PDF
        return create_individual_evaluation_pdf(data, options)

async def generate_enhanced_pdf(data: Dict, options: Dict) -> bytes:
    """Generate enhanced PDF with template-specific formatting"""
    
    # For now, use the existing PDF generator with enhanced options
    # In a full implementation, this would have template-specific PDF generation
    enhanced_options = {
        "include_comments": True,
        "include_scores": True,
        "template": options.get("template", "standard"),
        "styling": data.get("styling", {}),
        "metadata": data.get("export_metadata", {}),
        "content_config": data.get("content_config", {})
    }
    
    return create_individual_evaluation_pdf(data, enhanced_options)

async def generate_enhanced_excel(data: Dict, options: Dict) -> bytes:
    """Generate enhanced Excel export"""
    # Placeholder for enhanced Excel generation
    # This would implement Excel export with template-specific formatting
    from io import BytesIO
    content = b"Enhanced Excel export placeholder"
    return content

async def generate_enhanced_word(data: Dict, options: Dict) -> bytes:
    """Generate enhanced Word document"""
    # Placeholder for Word document generation
    from io import BytesIO
    content = b"Enhanced Word document placeholder"
    return content

async def generate_enhanced_html(data: Dict, options: Dict) -> str:
    """Generate enhanced HTML export"""
    # Placeholder for HTML generation
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Enhanced HTML Export</title>
        <style>
            body { font-family: Arial, sans-serif; }
            .header { background-color: #f0f0f0; padding: 20px; }
            .content { padding: 20px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Enhanced HTML Export</h1>
        </div>
        <div class="content">
            <p>This is a placeholder for enhanced HTML export.</p>
        </div>
    </body>
    </html>
    """