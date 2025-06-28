"""
AI 평가 실행 권한 제어 API 엔드포인트
관리자와 간사가 AI 자동 평가를 실행하고 제어하는 시스템
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from typing import List, Dict, Any, Optional
import logging
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import uuid
import asyncio
import json

from models import User
from security import get_current_user
from enhanced_permissions import Permission, check_permission, permission_checker

logger = logging.getLogger(__name__)

# AI 평가 제어 라우터 생성
ai_evaluation_control_router = APIRouter(prefix="/api/ai-evaluation", tags=["AI 평가 제어"])

# AI 평가 관련 모델들
class AIEvaluationRequest(BaseModel):
    """AI 평가 실행 요청"""
    evaluation_ids: List[str] = Field(..., description="평가 ID 목록")
    template_id: str = Field(..., description="평가 템플릿 ID")
    ai_provider: Optional[str] = Field(None, description="사용할 AI 공급자")
    ai_model: Optional[str] = Field(None, description="사용할 AI 모델")
    evaluation_mode: str = Field("comprehensive", description="평가 모드: comprehensive, quick, detailed")
    include_file_analysis: bool = Field(True, description="파일 분석 포함 여부")
    custom_prompt: Optional[str] = Field(None, description="커스텀 프롬프트")

class AIEvaluationJobConfig(BaseModel):
    """AI 평가 작업 설정"""
    max_concurrent_evaluations: int = Field(3, description="동시 실행 평가 수")
    timeout_minutes: int = Field(30, description="평가 타임아웃 (분)")
    retry_count: int = Field(2, description="재시도 횟수")
    quality_threshold: float = Field(0.8, description="품질 임계값")
    auto_approve: bool = Field(False, description="자동 승인 여부")

class AIEvaluationJob(BaseModel):
    """AI 평가 작업"""
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_data: AIEvaluationRequest
    config: AIEvaluationJobConfig
    status: str = Field("pending", description="작업 상태")
    progress: int = Field(0, description="진행률 (0-100)")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: str = Field(..., description="작업 생성자 ID")
    
    # 결과 정보
    total_evaluations: int = 0
    completed_evaluations: int = 0
    failed_evaluations: int = 0
    average_score: Optional[float] = None
    error_messages: List[str] = Field(default_factory=list)
    
    # 품질 메트릭
    confidence_scores: List[float] = Field(default_factory=list)
    processing_times: List[float] = Field(default_factory=list)

class AIEvaluationResult(BaseModel):
    """AI 평가 결과"""
    evaluation_id: str
    ai_scores: Dict[str, float] = Field(default_factory=dict)
    ai_comments: Dict[str, str] = Field(default_factory=dict)
    total_ai_score: float
    confidence_score: float
    processing_time_seconds: float
    ai_provider_used: str
    ai_model_used: str
    evaluation_timestamp: datetime
    
    # 분석 상세 정보
    file_analysis_results: Optional[Dict[str, Any]] = None
    criteria_analysis: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)

class AIEvaluationApproval(BaseModel):
    """AI 평가 승인/거부"""
    evaluation_id: str
    action: str = Field(..., description="approve 또는 reject")
    reason: Optional[str] = Field(None, description="승인/거부 사유")
    score_adjustments: Optional[Dict[str, float]] = Field(None, description="점수 조정")

# 작업 저장소 (실제로는 데이터베이스 사용)
ai_evaluation_jobs = {}
ai_evaluation_results = {}

async def check_ai_evaluation_permission(user: User, action: str, project_id: str = None) -> bool:
    """AI 평가 권한 확인"""
    try:
        # 관리자는 모든 권한
        if user.role == "admin":
            return True
        
        # 간사는 프로젝트별 권한
        if user.role == "secretary":
            if action in ["execute", "approve", "view"]:
                return await permission_checker.has_permission(
                    user, Permission.AI_ANALYSIS_EXECUTE, project_id
                )
        
        # 평가위원은 조회만 가능
        if user.role == "evaluator" and action == "view":
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"AI 평가 권한 확인 오류: {e}")
        return False

async def get_available_ai_providers():
    """사용 가능한 AI 공급자 목록 조회"""
    try:
        from server import db
        
        providers = await db.ai_providers.find({
            "is_active": True,
            "status": "enabled"
        }).sort("priority", 1).to_list(length=None)
        
        return providers
        
    except Exception as e:
        logger.error(f"AI 공급자 조회 오류: {e}")
        return []

async def analyze_file_content(file_path: str, evaluation_criteria: List[Dict]) -> Dict[str, Any]:
    """파일 내용 AI 분석"""
    try:
        # AI 서비스 사용하여 파일 분석
        from ai_service_enhanced import enhanced_ai_service
        
        # 파일 내용 읽기
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # AI 프롬프트 생성
        analysis_prompt = f"""
        다음 문서를 분석하여 평가 기준에 따라 점수를 매기세요.
        
        평가 기준:
        {json.dumps(evaluation_criteria, ensure_ascii=False, indent=2)}
        
        각 기준에 대해:
        1. 점수 (0-100)
        2. 근거
        3. 개선 권장사항
        
        JSON 형식으로 응답해주세요.
        """
        
        # AI 분석 실행
        response = await enhanced_ai_service.analyze_document(
            content=file_content,
            prompt=analysis_prompt,
            analysis_type="evaluation"
        )
        
        return {
            "analysis_result": response,
            "file_size": len(file_content),
            "analysis_timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"파일 분석 오류: {e}")
        return {
            "error": str(e),
            "analysis_timestamp": datetime.utcnow()
        }

async def execute_ai_evaluation(evaluation_id: str, template: Dict, config: Dict) -> AIEvaluationResult:
    """단일 평가에 대한 AI 평가 실행"""
    start_time = datetime.utcnow()
    
    try:
        from server import db
        
        # 평가 정보 조회
        evaluation = await db.evaluations.find_one({"_id": evaluation_id})
        if not evaluation:
            raise ValueError(f"평가를 찾을 수 없습니다: {evaluation_id}")
        
        # 기업 정보 조회
        company = await db.companies.find_one({"_id": evaluation.get("company_id")})
        
        # 업로드된 파일 목록 조회
        files = await db.files.find({"company_id": evaluation.get("company_id")}).to_list(length=None)
        
        # AI 서비스 초기화
        from ai_service_enhanced import enhanced_ai_service
        
        # 평가 기준 추출
        criteria = template.get("criteria", [])
        
        # 파일 분석 (옵션)
        file_analysis = {}
        if config.get("include_file_analysis", True) and files:
            for file_info in files[:3]:  # 최대 3개 파일만 분석
                file_path = file_info.get("file_path")
                if file_path:
                    analysis = await analyze_file_content(file_path, criteria)
                    file_analysis[file_info.get("file_name", "unknown")] = analysis
        
        # AI 평가 프롬프트 생성
        evaluation_prompt = f"""
        기업 평가를 수행해주세요.
        
        기업 정보:
        - 이름: {company.get('name', '알 수 없음')}
        - 업종: {company.get('business_type', '알 수 없음')}
        - 규모: {company.get('company_size', '알 수 없음')}
        
        평가 기준:
        {json.dumps(criteria, ensure_ascii=False, indent=2)}
        
        파일 분석 결과:
        {json.dumps(file_analysis, ensure_ascii=False, indent=2)}
        
        각 평가 기준에 대해 다음을 제공하세요:
        1. 점수 (0-{max([c.get('max_score', 100) for c in criteria])})
        2. 평가 근거
        3. 강점과 약점
        4. 개선 권장사항
        
        또한 전체적인 종합 의견과 위험 요소를 포함하세요.
        
        JSON 형식으로 응답해주세요.
        """
        
        # AI 평가 실행
        ai_response = await enhanced_ai_service.evaluate_business(
            prompt=evaluation_prompt,
            criteria=criteria,
            provider=config.get("ai_provider"),
            model=config.get("ai_model")
        )
        
        # 응답 파싱
        if isinstance(ai_response, str):
            try:
                ai_response = json.loads(ai_response)
            except json.JSONDecodeError:
                raise ValueError("AI 응답을 파싱할 수 없습니다")
        
        # 점수 및 코멘트 추출
        ai_scores = {}
        ai_comments = {}
        total_score = 0
        
        for criterion in criteria:
            criterion_id = criterion.get("id")
            criterion_name = criterion.get("name")
            
            # AI 응답에서 해당 기준의 점수와 코멘트 추출
            criterion_result = ai_response.get(criterion_name, {})
            score = criterion_result.get("score", 0)
            comment = criterion_result.get("comment", "")
            
            ai_scores[criterion_id] = score
            ai_comments[criterion_id] = comment
            
            # 가중치 적용
            weight = criterion.get("weight", 1.0)
            total_score += score * weight
        
        # 신뢰도 점수 계산 (예시 로직)
        confidence_score = min(0.95, 0.7 + (len(file_analysis) * 0.1))
        
        # 처리 시간 계산
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # 결과 객체 생성
        result = AIEvaluationResult(
            evaluation_id=evaluation_id,
            ai_scores=ai_scores,
            ai_comments=ai_comments,
            total_ai_score=total_score,
            confidence_score=confidence_score,
            processing_time_seconds=processing_time,
            ai_provider_used=config.get("ai_provider", "default"),
            ai_model_used=config.get("ai_model", "default"),
            evaluation_timestamp=datetime.utcnow(),
            file_analysis_results=file_analysis,
            criteria_analysis=ai_response.get("criteria_analysis", {}),
            recommendations=ai_response.get("recommendations", []),
            risk_factors=ai_response.get("risk_factors", [])
        )
        
        # 결과 저장
        ai_evaluation_results[evaluation_id] = result
        
        # 데이터베이스에 AI 평가 결과 저장
        await db.ai_evaluation_results.insert_one(result.dict())
        
        logger.info(f"AI 평가 완료: {evaluation_id}, 점수: {total_score:.2f}, 신뢰도: {confidence_score:.2f}")
        
        return result
        
    except Exception as e:
        logger.error(f"AI 평가 실행 오류 ({evaluation_id}): {e}")
        raise

async def process_ai_evaluation_job(job_id: str, request_data: AIEvaluationRequest, config: AIEvaluationJobConfig, user: User):
    """AI 평가 작업 처리"""
    try:
        job = ai_evaluation_jobs[job_id]
        job["status"] = "processing"
        job["started_at"] = datetime.utcnow()
        job["total_evaluations"] = len(request_data.evaluation_ids)
        
        from server import db
        
        # 템플릿 조회
        template = await db.evaluation_templates.find_one({"_id": request_data.template_id})
        if not template:
            raise ValueError(f"템플릿을 찾을 수 없습니다: {request_data.template_id}")
        
        # AI 공급자 설정
        providers = await get_available_ai_providers()
        if not providers and not request_data.ai_provider:
            raise ValueError("사용 가능한 AI 공급자가 없습니다")
        
        provider = request_data.ai_provider or providers[0].get("name")
        model = request_data.ai_model or "default"
        
        # 평가 설정
        eval_config = {
            "ai_provider": provider,
            "ai_model": model,
            "evaluation_mode": request_data.evaluation_mode,
            "include_file_analysis": request_data.include_file_analysis,
            "custom_prompt": request_data.custom_prompt
        }
        
        # 동시 실행 제한
        semaphore = asyncio.Semaphore(config.max_concurrent_evaluations)
        
        async def evaluate_single(evaluation_id: str):
            async with semaphore:
                try:
                    result = await execute_ai_evaluation(evaluation_id, template, eval_config)
                    job["completed_evaluations"] += 1
                    job["confidence_scores"].append(result.confidence_score)
                    job["processing_times"].append(result.processing_time_seconds)
                    return result
                except Exception as e:
                    job["failed_evaluations"] += 1
                    job["error_messages"].append(f"{evaluation_id}: {str(e)}")
                    logger.error(f"개별 평가 실패 ({evaluation_id}): {e}")
                    return None
                finally:
                    # 진행률 업데이트
                    completed = job["completed_evaluations"] + job["failed_evaluations"]
                    job["progress"] = int((completed / job["total_evaluations"]) * 100)
        
        # 모든 평가 병렬 실행
        tasks = [evaluate_single(eval_id) for eval_id in request_data.evaluation_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 평균 점수 계산
        valid_results = [r for r in results if isinstance(r, AIEvaluationResult)]
        if valid_results:
            job["average_score"] = sum(r.total_ai_score for r in valid_results) / len(valid_results)
        
        # 작업 완료
        job["status"] = "completed" if job["failed_evaluations"] == 0 else "completed_with_errors"
        job["completed_at"] = datetime.utcnow()
        job["progress"] = 100
        
        logger.info(f"AI 평가 작업 완료: {job_id}, 성공: {job['completed_evaluations']}, 실패: {job['failed_evaluations']}")
        
    except Exception as e:
        job["status"] = "failed"
        job["error_messages"].append(f"작업 실행 오류: {str(e)}")
        logger.error(f"AI 평가 작업 실패: {job_id}, 오류: {e}")

@ai_evaluation_control_router.post("/execute")
async def execute_ai_evaluations(
    request_data: AIEvaluationRequest,
    background_tasks: BackgroundTasks,
    config: AIEvaluationJobConfig = AIEvaluationJobConfig(),
    current_user: User = Depends(get_current_user)
):
    """AI 평가 실행"""
    try:
        # 권한 확인
        has_permission = await check_ai_evaluation_permission(current_user, "execute")
        if not has_permission:
            raise HTTPException(status_code=403, detail="AI 평가 실행 권한이 없습니다")
        
        # 평가 ID 유효성 검사
        if not request_data.evaluation_ids:
            raise HTTPException(status_code=400, detail="평가 ID가 필요합니다")
        
        # 작업 생성
        job_id = str(uuid.uuid4())
        job_data = AIEvaluationJob(
            job_id=job_id,
            request_data=request_data,
            config=config,
            created_by=current_user.id
        ).dict()
        
        ai_evaluation_jobs[job_id] = job_data
        
        # 백그라운드 작업 시작
        background_tasks.add_task(
            process_ai_evaluation_job,
            job_id,
            request_data,
            config,
            current_user
        )
        
        logger.info(f"AI 평가 작업 시작: {job_id}", extra={
            'user_id': current_user.id,
            'evaluation_count': len(request_data.evaluation_ids),
            'template_id': request_data.template_id
        })
        
        return {
            "success": True,
            "job_id": job_id,
            "message": f"{len(request_data.evaluation_ids)}개 평가에 대한 AI 분석이 시작되었습니다",
            "estimated_completion_time": len(request_data.evaluation_ids) * 2  # 평가당 2분 예상
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI 평가 실행 오류: {e}")
        raise HTTPException(status_code=500, detail="AI 평가 실행 중 오류가 발생했습니다")

@ai_evaluation_control_router.get("/jobs/{job_id}")
async def get_ai_evaluation_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """AI 평가 작업 상태 조회"""
    try:
        # 권한 확인
        has_permission = await check_ai_evaluation_permission(current_user, "view")
        if not has_permission:
            raise HTTPException(status_code=403, detail="AI 평가 작업 조회 권한이 없습니다")
        
        if job_id not in ai_evaluation_jobs:
            raise HTTPException(status_code=404, detail="AI 평가 작업을 찾을 수 없습니다")
        
        job_data = ai_evaluation_jobs[job_id]
        
        return {
            "success": True,
            "job": job_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI 평가 작업 상태 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="AI 평가 작업 상태 조회 중 오류가 발생했습니다")

@ai_evaluation_control_router.get("/jobs")
async def get_ai_evaluation_jobs(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, le=100),
    status: Optional[str] = Query(None)
):
    """AI 평가 작업 목록 조회"""
    try:
        # 권한 확인
        has_permission = await check_ai_evaluation_permission(current_user, "view")
        if not has_permission:
            raise HTTPException(status_code=403, detail="AI 평가 작업 목록 조회 권한이 없습니다")
        
        # 작업 목록 필터링
        jobs = []
        for job_data in ai_evaluation_jobs.values():
            if status and job_data["status"] != status:
                continue
                
            # 일반 사용자는 자신의 작업만 조회
            if current_user.role not in ["admin"] and job_data["created_by"] != current_user.id:
                continue
                
            jobs.append(job_data)
        
        # 생성일 기준 내림차순 정렬
        jobs.sort(key=lambda x: x.get("started_at", x.get("created_at", datetime.min)), reverse=True)
        
        # 제한된 수만 반환
        jobs = jobs[:limit]
        
        return {
            "success": True,
            "jobs": jobs,
            "total": len(jobs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI 평가 작업 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="AI 평가 작업 목록 조회 중 오류가 발생했습니다")

@ai_evaluation_control_router.get("/results/{evaluation_id}")
async def get_ai_evaluation_result(
    evaluation_id: str,
    current_user: User = Depends(get_current_user)
):
    """AI 평가 결과 조회"""
    try:
        # 권한 확인
        has_permission = await check_ai_evaluation_permission(current_user, "view")
        if not has_permission:
            raise HTTPException(status_code=403, detail="AI 평가 결과 조회 권한이 없습니다")
        
        if evaluation_id not in ai_evaluation_results:
            raise HTTPException(status_code=404, detail="AI 평가 결과를 찾을 수 없습니다")
        
        result = ai_evaluation_results[evaluation_id]
        
        return {
            "success": True,
            "result": result.dict() if hasattr(result, 'dict') else result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI 평가 결과 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="AI 평가 결과 조회 중 오류가 발생했습니다")

@ai_evaluation_control_router.post("/approve")
async def approve_ai_evaluation(
    approval_data: AIEvaluationApproval,
    current_user: User = Depends(get_current_user)
):
    """AI 평가 결과 승인/거부"""
    try:
        # 권한 확인 (관리자 또는 간사만)
        if current_user.role not in ["admin", "secretary"]:
            raise HTTPException(status_code=403, detail="AI 평가 승인 권한이 없습니다")
        
        from server import db
        
        # 평가 존재 확인
        evaluation = await db.evaluations.find_one({"_id": approval_data.evaluation_id})
        if not evaluation:
            raise HTTPException(status_code=404, detail="평가를 찾을 수 없습니다")
        
        # AI 평가 결과 확인
        if approval_data.evaluation_id not in ai_evaluation_results:
            raise HTTPException(status_code=404, detail="AI 평가 결과를 찾을 수 없습니다")
        
        ai_result = ai_evaluation_results[approval_data.evaluation_id]
        
        # 승인/거부 처리
        if approval_data.action == "approve":
            # AI 점수를 실제 평가 점수로 적용
            update_data = {
                "ai_evaluation_approved": True,
                "ai_evaluation_approved_by": current_user.id,
                "ai_evaluation_approved_at": datetime.utcnow(),
                "ai_total_score": ai_result.total_ai_score if hasattr(ai_result, 'total_ai_score') else ai_result.get('total_ai_score'),
                "ai_scores": ai_result.ai_scores if hasattr(ai_result, 'ai_scores') else ai_result.get('ai_scores'),
                "ai_comments": ai_result.ai_comments if hasattr(ai_result, 'ai_comments') else ai_result.get('ai_comments')
            }
            
            # 점수 조정이 있는 경우
            if approval_data.score_adjustments:
                for criterion_id, adjusted_score in approval_data.score_adjustments.items():
                    update_data["ai_scores"][criterion_id] = adjusted_score
                
                # 총점 재계산
                template = await db.evaluation_templates.find_one({"_id": evaluation.get("template_id")})
                if template:
                    total_score = 0
                    for criterion in template.get("criteria", []):
                        criterion_id = criterion.get("id")
                        score = update_data["ai_scores"].get(criterion_id, 0)
                        weight = criterion.get("weight", 1.0)
                        total_score += score * weight
                    update_data["ai_total_score"] = total_score
            
            message = "AI 평가 결과가 승인되었습니다"
            
        else:  # reject
            update_data = {
                "ai_evaluation_approved": False,
                "ai_evaluation_rejected": True,
                "ai_evaluation_rejected_by": current_user.id,
                "ai_evaluation_rejected_at": datetime.utcnow(),
                "ai_evaluation_rejection_reason": approval_data.reason
            }
            message = "AI 평가 결과가 거부되었습니다"
        
        # 평가 업데이트
        await db.evaluations.update_one(
            {"_id": approval_data.evaluation_id},
            {"$set": update_data}
        )
        
        logger.info(f"AI 평가 {approval_data.action}: {approval_data.evaluation_id}", extra={
            'user_id': current_user.id,
            'evaluation_id': approval_data.evaluation_id,
            'action': approval_data.action
        })
        
        return {
            "success": True,
            "message": message,
            "evaluation_id": approval_data.evaluation_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI 평가 승인/거부 오류: {e}")
        raise HTTPException(status_code=500, detail="AI 평가 승인/거부 중 오류가 발생했습니다")

@ai_evaluation_control_router.get("/providers")
async def get_ai_providers(current_user: User = Depends(get_current_user)):
    """사용 가능한 AI 공급자 목록 조회"""
    try:
        # 권한 확인
        has_permission = await check_ai_evaluation_permission(current_user, "view")
        if not has_permission:
            raise HTTPException(status_code=403, detail="AI 공급자 조회 권한이 없습니다")
        
        providers = await get_available_ai_providers()
        
        return {
            "success": True,
            "providers": providers
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI 공급자 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="AI 공급자 조회 중 오류가 발생했습니다")

@ai_evaluation_control_router.post("/jobs/{job_id}/cancel")
async def cancel_ai_evaluation_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """AI 평가 작업 취소"""
    try:
        # 권한 확인
        if current_user.role not in ["admin", "secretary"]:
            raise HTTPException(status_code=403, detail="AI 평가 작업 취소 권한이 없습니다")
        
        if job_id not in ai_evaluation_jobs:
            raise HTTPException(status_code=404, detail="AI 평가 작업을 찾을 수 없습니다")
        
        job = ai_evaluation_jobs[job_id]
        
        # 작업이 이미 완료된 경우
        if job["status"] in ["completed", "completed_with_errors", "failed"]:
            raise HTTPException(status_code=400, detail="이미 완료된 작업은 취소할 수 없습니다")
        
        # 작업 취소
        job["status"] = "cancelled"
        job["completed_at"] = datetime.utcnow()
        job["error_messages"].append(f"사용자 {current_user.user_name}에 의해 취소됨")
        
        logger.info(f"AI 평가 작업 취소: {job_id}", extra={
            'user_id': current_user.id,
            'job_id': job_id
        })
        
        return {
            "success": True,
            "message": "AI 평가 작업이 취소되었습니다",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI 평가 작업 취소 오류: {e}")
        raise HTTPException(status_code=500, detail="AI 평가 작업 취소 중 오류가 발생했습니다")

# 데이터베이스 연결
try:
    from server import db
except ImportError:
    db = None
    logger.warning("데이터베이스 연결을 찾을 수 없습니다")