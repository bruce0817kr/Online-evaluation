"""
AI 기능 API 엔드포인트
중소기업 지원사업 평가 시스템의 AI 기능들을 제공하는 REST API
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import aiofiles
import json
from datetime import datetime
import logging

from models import User
from security import get_current_user, check_admin_or_secretary
from enhanced_permissions import (
    Permission, check_permission, check_ai_execution_permission,
    permission_checker
)

logger = logging.getLogger(__name__)

try:
    from ai_service_enhanced import enhanced_ai_service as ai_service
    logger.info("향상된 AI 서비스를 사용합니다.")
except ImportError:
    from ai_service import ai_service
    logger.warning("기본 AI 서비스를 사용합니다.")

# AI 라우터 생성
ai_router = APIRouter(prefix="/api/ai", tags=["AI 기능"])

# Pydantic 모델들
class DocumentAnalysisRequest(BaseModel):
    document_text: str = Field(..., description="분석할 문서 텍스트")
    document_type: str = Field("business_plan", description="문서 유형 (business_plan, technical_plan, financial_plan)")
    company_id: Optional[str] = Field(None, description="회사 ID")
    project_id: Optional[str] = Field(None, description="프로젝트 ID")

class ScoreSuggestionRequest(BaseModel):
    document_analysis: Dict[str, Any] = Field(..., description="문서 분석 결과")
    template_type: str = Field("digital_transformation", description="평가 템플릿 유형")
    evaluator_notes: Optional[str] = Field(None, description="평가자 추가 메모")

class PlagiarismCheckRequest(BaseModel):
    document_text: str = Field(..., description="검사할 문서 텍스트")
    project_id: Optional[str] = Field(None, description="프로젝트 ID (같은 프로젝트 내 문서들과 비교)")
    exclude_company_id: Optional[str] = Field(None, description="제외할 회사 ID (자신의 이전 문서 제외)")

class AIAnalysisResponse(BaseModel):
    success: bool
    analysis_id: str
    results: Dict[str, Any]
    processing_time: float
    ai_provider: str
    analyzed_at: str

@ai_router.post("/analyze-document", response_model=AIAnalysisResponse)
async def analyze_document(
    request: DocumentAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """문서 내용 AI 분석"""
    start_time = datetime.utcnow()
    
    try:
        # 향상된 권한 확인 - AI 분석 보기 권한
        has_permission = await permission_checker.has_permission(
            current_user, Permission.AI_ANALYSIS_VIEW, request.project_id
        )
        if not has_permission:
            raise HTTPException(status_code=403, detail="AI 분석 권한이 없습니다")
        
        # AI 분석 실행
        analysis_results = await ai_service.analyze_document_content(
            document_text=request.document_text,
            document_type=request.document_type
        )
        
        # 분석 결과 저장 (DB에 저장 - 추후 구현)
        analysis_id = f"analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{current_user.id[:8]}"
        
        # 처리 시간 계산
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # 분석 로그 저장
        logger.info(f"AI 문서 분석 완료", extra={
            'user_id': current_user.id,
            'analysis_id': analysis_id,
            'document_type': request.document_type,
            'processing_time': processing_time,
            'ai_provider': analysis_results.get('ai_provider', 'unknown')
        })
        
        return AIAnalysisResponse(
            success=True,
            analysis_id=analysis_id,
            results=analysis_results,
            processing_time=processing_time,
            ai_provider=analysis_results.get('ai_provider', 'fallback'),
            analyzed_at=start_time.isoformat()
        )
        
    except Exception as e:
        logger.error(f"AI 문서 분석 오류: {e}", extra={
            'user_id': current_user.id,
            'error': str(e)
        })
        raise HTTPException(status_code=500, detail=f"AI 분석 중 오류가 발생했습니다: {str(e)}")

@ai_router.post("/suggest-scores")
async def suggest_evaluation_scores(
    request: ScoreSuggestionRequest,
    current_user: User = Depends(get_current_user)
):
    """AI 기반 평가 점수 제안"""
    try:
        # 향상된 권한 확인 - AI 분석 보기 권한 (평가위원은 보기만 가능)
        has_permission = await permission_checker.has_permission(
            current_user, Permission.AI_ANALYSIS_VIEW
        )
        if not has_permission:
            raise HTTPException(status_code=403, detail="평가 점수 제안 권한이 없습니다")
        
        # AI 점수 제안 실행
        score_suggestions = await ai_service.suggest_evaluation_scores(
            document_analysis=request.document_analysis,
            template_type=request.template_type
        )
        
        # 제안자 정보 추가
        score_suggestions["suggested_by"] = current_user.id
        score_suggestions["evaluator_name"] = current_user.user_name
        
        logger.info(f"AI 점수 제안 완료", extra={
            'user_id': current_user.id,
            'template_type': request.template_type,
            'ai_provider': score_suggestions.get('ai_provider', 'unknown')
        })
        
        return {
            "success": True,
            "suggestions": score_suggestions,
            "disclaimer": "이 점수는 AI에 의한 제안입니다. 최종 평가는 평가위원의 판단에 따라 결정됩니다."
        }
        
    except Exception as e:
        logger.error(f"AI 점수 제안 오류: {e}", extra={
            'user_id': current_user.id,
            'error': str(e)
        })
        raise HTTPException(status_code=500, detail=f"점수 제안 중 오류가 발생했습니다: {str(e)}")

@ai_router.post("/check-plagiarism")
async def check_plagiarism(
    request: PlagiarismCheckRequest,
    current_user: User = Depends(get_current_user)
):
    """표절 및 유사도 검사"""
    try:
        # 향상된 권한 확인 - AI 분석 실행 권한 (관리자, 간사만 가능)
        has_permission = await permission_checker.has_permission(
            current_user, Permission.AI_ANALYSIS_EXECUTE, request.project_id
        )
        if not has_permission:
            raise HTTPException(status_code=403, detail="표절 검사 실행 권한이 없습니다")
        
        # 기존 문서들 조회 (실제 구현에서는 DB에서 조회)
        # TODO: 실제 프로젝트의 다른 회사 문서들을 조회하는 로직 구현
        existing_documents = [
            "샘플 문서 1의 내용입니다...",
            "샘플 문서 2의 내용입니다...",
        ]
        
        # 표절 검사 실행
        plagiarism_results = await ai_service.detect_plagiarism_similarity(
            document_text=request.document_text,
            existing_documents=existing_documents
        )
        
        logger.info(f"표절 검사 완료", extra={
            'user_id': current_user.id,
            'documents_checked': plagiarism_results.get('total_documents_checked', 0),
            'max_similarity': plagiarism_results.get('max_similarity', 0)
        })
        
        return {
            "success": True,
            "results": plagiarism_results,
            "recommendation": "높은 유사도가 발견된 경우 추가 검토가 필요합니다." if plagiarism_results.get('overall_risk') == 'high' else "유사도 검사 결과 문제없습니다."
        }
        
    except Exception as e:
        logger.error(f"표절 검사 오류: {e}", extra={
            'user_id': current_user.id,
            'error': str(e)
        })
        raise HTTPException(status_code=500, detail=f"표절 검사 중 오류가 발생했습니다: {str(e)}")

@ai_router.post("/extract-information")
async def extract_key_information(
    request: DocumentAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """문서에서 핵심 정보 자동 추출"""
    try:
        # 권한 확인
        if current_user.role not in ["admin", "secretary", "evaluator"]:
            raise HTTPException(status_code=403, detail="정보 추출 권한이 없습니다")
        
        # 정보 추출 실행
        extracted_info = await ai_service.extract_key_information(request.document_text)
        
        logger.info(f"정보 추출 완료", extra={
            'user_id': current_user.id,
            'document_type': request.document_type
        })
        
        return {
            "success": True,
            "extracted_information": extracted_info,
            "note": "추출된 정보는 참고용이며, 정확성을 위해 원본 문서를 확인해주세요."
        }
        
    except Exception as e:
        logger.error(f"정보 추출 오류: {e}", extra={
            'user_id': current_user.id,
            'error': str(e)
        })
        raise HTTPException(status_code=500, detail=f"정보 추출 중 오류가 발생했습니다: {str(e)}")

@ai_router.post("/analyze-file")
async def analyze_uploaded_file(
    file: UploadFile = File(...),
    document_type: str = "business_plan",
    current_user: User = Depends(get_current_user)
):
    """업로드된 파일 AI 분석"""
    try:
        # 권한 확인
        if current_user.role not in ["admin", "secretary", "evaluator"]:
            raise HTTPException(status_code=403, detail="파일 분석 권한이 없습니다")
        
        # 파일 타입 확인
        if not file.filename.lower().endswith(('.txt', '.pdf', '.docx')):
            raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다. (txt, pdf, docx만 지원)")
        
        # 파일 내용 읽기
        file_content = await file.read()
        
        # 텍스트 추출 (간단한 구현 - 실제로는 파일 타입별 처리 필요)
        if file.filename.lower().endswith('.txt'):
            text_content = file_content.decode('utf-8')
        else:
            # PDF, DOCX 처리는 별도 라이브러리 필요
            text_content = "파일 내용 추출을 위해서는 추가 라이브러리 설치가 필요합니다."
        
        # AI 분석 실행
        analysis_results = await ai_service.analyze_document_content(
            document_text=text_content,
            document_type=document_type
        )
        
        # 파일 정보 추가
        analysis_results["file_info"] = {
            "filename": file.filename,
            "file_size": len(file_content),
            "content_type": file.content_type
        }
        
        logger.info(f"파일 AI 분석 완료", extra={
            'user_id': current_user.id,
            'filename': file.filename,
            'file_size': len(file_content)
        })
        
        return {
            "success": True,
            "analysis": analysis_results,
            "file_info": analysis_results["file_info"]
        }
        
    except Exception as e:
        logger.error(f"파일 분석 오류: {e}", extra={
            'user_id': current_user.id,
            'filename': file.filename if file else 'unknown',
            'error': str(e)
        })
        raise HTTPException(status_code=500, detail=f"파일 분석 중 오류가 발생했습니다: {str(e)}")

@ai_router.get("/analysis-history")
async def get_analysis_history(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """AI 분석 히스토리 조회"""
    try:
        # TODO: 실제 DB에서 분석 히스토리 조회 구현
        # 현재는 샘플 데이터 반환
        
        sample_history = [
            {
                "analysis_id": f"analysis_20250621_{i:03d}",
                "document_type": "business_plan",
                "analyzed_at": f"2025-06-21T{10+i:02d}:30:00Z",
                "ai_provider": "openai" if i % 2 == 0 else "anthropic",
                "status": "completed"
            }
            for i in range(offset, min(offset + limit, 20))
        ]
        
        return {
            "success": True,
            "history": sample_history,
            "total": 20,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"분석 히스토리 조회 오류: {e}", extra={
            'user_id': current_user.id,
            'error': str(e)
        })
        raise HTTPException(status_code=500, detail=f"히스토리 조회 중 오류가 발생했습니다: {str(e)}")

@ai_router.get("/templates")
async def get_ai_templates(current_user: User = Depends(get_current_user)):
    """AI 평가 템플릿 목록 조회"""
    try:
        templates = ai_service.evaluation_templates
        
        return {
            "success": True,
            "templates": templates,
            "total": len(templates)
        }
        
    except Exception as e:
        logger.error(f"AI 템플릿 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="템플릿 조회 중 오류가 발생했습니다")

@ai_router.get("/status")
async def get_ai_service_status(current_user: User = Depends(get_current_user)):
    """AI 서비스 상태 확인"""
    try:
        # 평가위원도 상태 확인 가능하도록 권한 완화
        if current_user.role not in ["admin", "secretary", "evaluator"]:
            raise HTTPException(status_code=403, detail="AI 서비스 상태 확인 권한이 없습니다")
        
        # AI 서비스 객체 안전 접근
        openai_available = False
        anthropic_available = False
        templates_loaded = 0
        
        try:
            openai_available = hasattr(ai_service, 'openai_client') and ai_service.openai_client is not None
            anthropic_available = hasattr(ai_service, 'anthropic_client') and ai_service.anthropic_client is not None
            templates_loaded = len(getattr(ai_service, 'evaluation_templates', {}))
        except Exception as attr_error:
            logger.warning(f"AI 서비스 속성 접근 오류: {attr_error}")
        
        status = {
            "openai_available": openai_available,
            "anthropic_available": anthropic_available,
            "fallback_mode": not openai_available and not anthropic_available,
            "templates_loaded": templates_loaded,
            "service_status": "operational" if (openai_available or anthropic_available) else "limited"
        }
        
        return {
            "success": True,
            "status": status,
            "message": "AI 서비스가 정상 작동 중입니다." if status["service_status"] == "operational" else "제한된 기능으로 동작 중입니다. API 키를 확인해주세요."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI 서비스 상태 확인 오류: {e}")
        # 오류 시 기본 상태 반환
        return {
            "success": False,
            "status": {
                "openai_available": False,
                "anthropic_available": False,
                "fallback_mode": True,
                "templates_loaded": 0,
                "service_status": "error"
            },
            "message": f"상태 확인 중 오류가 발생했습니다: {str(e)}"
        }