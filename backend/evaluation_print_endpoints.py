"""
평가표 출력/저장 API 엔드포인트
개별, 전체, 위원장용 평가표 PDF 생성 및 다운로드
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from typing import List, Dict, Any, Optional
import logging
from pydantic import BaseModel, Field
from datetime import datetime
import os
import uuid
import asyncio
from io import BytesIO
import json

# PDF 생성 라이브러리 (reportlab 사용)
try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib.colors import black, white, grey, lightgrey
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    PDF_ENABLED = True
except ImportError:
    PDF_ENABLED = False
    print("⚠️ PDF 생성 라이브러리가 설치되지 않았습니다. pip install reportlab을 실행하세요.")

from models import User
from security import get_current_user
from enhanced_permissions import Permission, check_permission, permission_checker

logger = logging.getLogger(__name__)

# 평가표 출력 라우터 생성 - Fixed prefix to avoid conflict with evaluation_api.py
evaluation_print_router = APIRouter(prefix="/api/evaluations/print", tags=["평가표 출력"])

# 데이터베이스 연결
try:
    from server import db
except ImportError:
    db = None
    logger.warning("데이터베이스 연결을 찾을 수 없습니다")

# 평가 목록 조회 엔드포인트
@evaluation_print_router.get("/list")
async def get_evaluations_list(
    project_id: Optional[str] = Query(None, description="프로젝트 ID 필터"),
    current_user: User = Depends(get_current_user)
):
    """평가 목록 조회"""
    try:
        if not db:
            raise HTTPException(status_code=500, detail="데이터베이스 연결이 없습니다")
            
        # evaluation_sheets 컬렉션에서 조회
        query = {}
        if project_id:
            query["project_id"] = project_id
            
        evaluations = await db.evaluation_sheets.find(query).to_list(1000)
        
        # 만약 evaluation_sheets가 비어있다면 evaluations 컬렉션에서 조회
        if not evaluations:
            evaluations = await db.evaluations.find(query).to_list(1000)
            
        return evaluations
    except Exception as e:
        logger.error(f"평가 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"평가 목록 조회 실패: {str(e)}")

# 요청 모델들
class EvaluationPrintRequest(BaseModel):
    """평가표 출력 요청"""
    evaluation_ids: List[str] = Field(..., description="평가 ID 목록")
    print_type: str = Field(..., description="출력 타입: individual, bulk, chairman")
    include_scores: bool = Field(True, description="점수 포함 여부")
    include_comments: bool = Field(True, description="코멘트 포함 여부")
    format: str = Field("pdf", description="출력 형식: pdf, excel")
    template_options: Optional[Dict[str, Any]] = Field(None, description="템플릿 옵션")

class ChairmanSummaryRequest(BaseModel):
    """위원장 종합 평가표 요청"""
    project_id: str = Field(..., description="프로젝트 ID")
    evaluation_ids: Optional[List[str]] = Field(None, description="특정 평가 ID 목록")
    include_statistics: bool = Field(True, description="통계 정보 포함")
    include_rankings: bool = Field(True, description="순위 정보 포함")
    include_detailed_scores: bool = Field(True, description="상세 점수 포함")

class PrintJobStatus(BaseModel):
    """출력 작업 상태"""
    job_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: int = 0
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

# 출력 작업 상태 저장소 (실제로는 Redis나 데이터베이스 사용)
print_jobs = {}

def setup_korean_fonts():
    """한글 폰트 설정"""
    try:
        # 시스템 폰트 경로들
        font_paths = [
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",  # Ubuntu
            "/System/Library/Fonts/AppleGothic.ttf",  # macOS
            "C:/Windows/Fonts/malgun.ttf",  # Windows
            "./fonts/NanumGothic.ttf"  # 로컬 폰트
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Korean', font_path))
                return True
        
        # 기본 폰트 사용
        logger.warning("한글 폰트를 찾을 수 없어 기본 폰트를 사용합니다.")
        return False
    except Exception as e:
        logger.error(f"폰트 설정 오류: {e}")
        return False

def create_pdf_styles():
    """PDF 스타일 생성"""
    styles = getSampleStyleSheet()
    
    # 한글 폰트 사용 여부에 따라 폰트 설정
    font_name = 'Korean' if setup_korean_fonts() else 'Helvetica'
    
    # 커스텀 스타일 정의
    styles.add(ParagraphStyle(
        name='KoreanTitle',
        fontName=font_name,
        fontSize=16,
        spaceAfter=12,
        alignment=1,  # 중앙 정렬
        textColor=colors.black
    ))
    
    styles.add(ParagraphStyle(
        name='KoreanHeading',
        fontName=font_name,
        fontSize=12,
        spaceBefore=6,
        spaceAfter=6,
        textColor=colors.black
    ))
    
    styles.add(ParagraphStyle(
        name='KoreanNormal',
        fontName=font_name,
        fontSize=10,
        spaceAfter=6,
        textColor=colors.black
    ))
    
    styles.add(ParagraphStyle(
        name='KoreanSmall',
        fontName=font_name,
        fontSize=8,
        spaceAfter=4,
        textColor=colors.grey
    ))
    
    return styles

async def get_evaluation_data(evaluation_id: str) -> Dict[str, Any]:
    """평가 데이터 조회"""
    try:
        from server import db
        
        # 평가 기본 정보 조회
        evaluation = await db.evaluations.find_one({"_id": evaluation_id})
        if not evaluation:
            raise ValueError(f"평가를 찾을 수 없습니다: {evaluation_id}")
        
        # 평가자 정보 조회
        evaluator = await db.users.find_one({"_id": evaluation.get("evaluator_id")})
        
        # 기업 정보 조회
        company = await db.companies.find_one({"_id": evaluation.get("company_id")})
        
        # 프로젝트 정보 조회
        project = await db.projects.find_one({"_id": evaluation.get("project_id")})
        
        # 템플릿 정보 조회
        template = await db.evaluation_templates.find_one({"_id": evaluation.get("template_id")})
        
        # 평가 점수 조회
        scores = await db.evaluation_scores.find({"evaluation_id": evaluation_id}).to_list(length=None)
        
        return {
            "evaluation": evaluation,
            "evaluator": evaluator,
            "company": company,
            "project": project,
            "template": template,
            "scores": scores
        }
        
    except Exception as e:
        logger.error(f"평가 데이터 조회 오류: {e}")
        raise

def create_individual_evaluation_pdf(evaluation_data: Dict[str, Any], options: Dict[str, Any] = None) -> bytes:
    """개별 평가표 PDF 생성"""
    if not PDF_ENABLED:
        raise HTTPException(status_code=500, detail="PDF 생성 기능이 비활성화되어 있습니다")
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
    
    # 스타일 설정
    styles = create_pdf_styles()
    story = []
    
    evaluation = evaluation_data["evaluation"]
    evaluator = evaluation_data["evaluator"]
    company = evaluation_data["company"]
    project = evaluation_data["project"]
    template = evaluation_data["template"]
    scores = evaluation_data["scores"]
    
    # 제목
    title = f"평가표 - {company.get('name', '알 수 없음')}"
    story.append(Paragraph(title, styles['KoreanTitle']))
    story.append(Spacer(1, 12))
    
    # 기본 정보 테이블
    basic_info_data = [
        ['항목', '내용'],
        ['프로젝트명', project.get('name', '알 수 없음')],
        ['기업명', company.get('name', '알 수 없음')],
        ['평가자', evaluator.get('user_name', '알 수 없음')],
        ['평가일', evaluation.get('created_at', datetime.utcnow()).strftime('%Y-%m-%d %H:%M')],
        ['평가 상태', evaluation.get('status', '알 수 없음')]
    ]
    
    basic_info_table = Table(basic_info_data, colWidths=[4*cm, 12*cm])
    basic_info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Korean' if setup_korean_fonts() else 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(basic_info_table)
    story.append(Spacer(1, 20))
    
    # 평가 기준 및 점수
    if template and template.get('criteria'):
        story.append(Paragraph("평가 기준 및 점수", styles['KoreanHeading']))
        
        # 점수 데이터를 딕셔너리로 변환
        score_dict = {score.get('criterion_id'): score for score in scores}
        
        criteria_data = [['평가 항목', '배점', '획득 점수', '가중치', '비고']]
        total_score = 0
        max_total_score = 0
        
        for criterion in template['criteria']:
            criterion_id = criterion.get('id')
            score_data = score_dict.get(criterion_id, {})
            
            name = criterion.get('name', '알 수 없음')
            max_score = criterion.get('max_score', 0)
            weight = criterion.get('weight', 1.0)
            bonus = '가점' if criterion.get('bonus', False) else ''
            
            achieved_score = score_data.get('score', 0)
            weighted_score = achieved_score * weight
            
            criteria_data.append([
                name,
                f"{max_score}점",
                f"{achieved_score}점",
                f"x{weight}",
                bonus
            ])
            
            if not criterion.get('bonus', False):
                total_score += weighted_score
                max_total_score += max_score * weight
        
        # 총점 행 추가
        criteria_data.append([
            '총점',
            f"{max_total_score}점",
            f"{total_score}점",
            '',
            f"{(total_score/max_total_score*100):.1f}%" if max_total_score > 0 else "0%"
        ])
        
        criteria_table = Table(criteria_data, colWidths=[5*cm, 2*cm, 2.5*cm, 2*cm, 4.5*cm])
        criteria_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Korean' if setup_korean_fonts() else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, -1), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT')  # 첫 번째 열은 왼쪽 정렬
        ]))
        
        story.append(criteria_table)
        story.append(Spacer(1, 20))
    
    # 종합 의견
    if options and options.get('include_comments', True):
        story.append(Paragraph("종합 의견", styles['KoreanHeading']))
        
        comments = evaluation.get('comments', '작성된 의견이 없습니다.')
        story.append(Paragraph(comments, styles['KoreanNormal']))
        story.append(Spacer(1, 20))
    
    # 서명 영역
    signature_data = [
        ['평가자 서명', ''],
        ['날짜', datetime.now().strftime('%Y년 %m월 %d일')]
    ]
    
    signature_table = Table(signature_data, colWidths=[4*cm, 12*cm])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Korean' if setup_korean_fonts() else 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LINEBELOW', (1, 0), (1, 0), 1, colors.black),  # 서명란 밑줄
    ]))
    
    story.append(signature_table)
    
    # PDF 생성
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def create_chairman_summary_pdf(project_data: Dict[str, Any], options: Dict[str, Any] = None) -> bytes:
    """위원장 종합 평가표 PDF 생성"""
    if not PDF_ENABLED:
        raise HTTPException(status_code=500, detail="PDF 생성 기능이 비활성화되어 있습니다")
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
    
    # 스타일 설정
    styles = create_pdf_styles()
    story = []
    
    project = project_data["project"]
    evaluations = project_data["evaluations"]
    companies = project_data["companies"]
    
    # 제목
    title = f"평가위원장 종합 평가표 - {project.get('name', '알 수 없음')}"
    story.append(Paragraph(title, styles['KoreanTitle']))
    story.append(Spacer(1, 12))
    
    # 프로젝트 정보
    project_info_data = [
        ['항목', '내용'],
        ['프로젝트명', project.get('name', '알 수 없음')],
        ['평가 기간', f"{project.get('start_date', '알 수 없음')} ~ {project.get('end_date', '알 수 없음')}"],
        ['총 평가 건수', f"{len(evaluations)}건"],
        ['작성일', datetime.now().strftime('%Y년 %m월 %d일')]
    ]
    
    project_info_table = Table(project_info_data, colWidths=[4*cm, 12*cm])
    project_info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Korean' if setup_korean_fonts() else 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(project_info_table)
    story.append(Spacer(1, 20))
    
    # 평가 결과 요약
    if options and options.get('include_statistics', True):
        story.append(Paragraph("평가 결과 요약", styles['KoreanHeading']))
        
        # 기업별 점수 집계
        company_scores = {}
        for evaluation in evaluations:
            company_id = evaluation.get('company_id')
            if company_id not in company_scores:
                company_scores[company_id] = []
            
            total_score = evaluation.get('total_score', 0)
            company_scores[company_id].append(total_score)
        
        # 요약 테이블 데이터
        summary_data = [['순위', '기업명', '평균 점수', '최고 점수', '최저 점수', '평가 횟수']]
        
        # 평균 점수로 정렬
        sorted_companies = []
        for company_id, scores in company_scores.items():
            company = companies.get(company_id, {})
            avg_score = sum(scores) / len(scores) if scores else 0
            max_score = max(scores) if scores else 0
            min_score = min(scores) if scores else 0
            
            sorted_companies.append({
                'company_name': company.get('name', '알 수 없음'),
                'avg_score': avg_score,
                'max_score': max_score,
                'min_score': min_score,
                'count': len(scores)
            })
        
        sorted_companies.sort(key=lambda x: x['avg_score'], reverse=True)
        
        for i, company in enumerate(sorted_companies, 1):
            summary_data.append([
                str(i),
                company['company_name'],
                f"{company['avg_score']:.1f}점",
                f"{company['max_score']:.1f}점",
                f"{company['min_score']:.1f}점",
                f"{company['count']}회"
            ])
        
        summary_table = Table(summary_data, colWidths=[1.5*cm, 4*cm, 2.5*cm, 2.5*cm, 2.5*cm, 3*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Korean' if setup_korean_fonts() else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 0), (1, -1), 'LEFT')  # 기업명은 왼쪽 정렬
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
    
    # 위원장 의견
    story.append(Paragraph("위원장 종합 의견", styles['KoreanHeading']))
    
    opinion_text = """
    본 평가는 공정하고 객관적인 기준에 따라 실시되었으며, 
    각 기업의 사업성, 기술성, 혁신성 등을 종합적으로 검토하였습니다.
    
    평가 결과를 바탕으로 우수한 기업들이 선정되기를 권고하며,
    향후 지속적인 모니터링과 지원이 필요합니다.
    
    [위원장 의견을 입력하세요]
    """
    
    story.append(Paragraph(opinion_text, styles['KoreanNormal']))
    story.append(Spacer(1, 30))
    
    # 서명 영역
    signature_data = [
        ['평가위원장', ''],
        ['직책/소속', ''],
        ['서명', ''],
        ['날짜', datetime.now().strftime('%Y년 %m월 %d일')]
    ]
    
    signature_table = Table(signature_data, colWidths=[4*cm, 12*cm])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Korean' if setup_korean_fonts() else 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LINEBELOW', (1, 0), (1, 2), 1, colors.black),  # 서명란 밑줄
    ]))
    
    story.append(signature_table)
    
    # PDF 생성
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

async def process_print_job(job_id: str, request_data: Dict[str, Any], user: User):
    """비동기 출력 작업 처리"""
    try:
        print_jobs[job_id]["status"] = "processing"
        print_jobs[job_id]["progress"] = 10
        
        from server import db
        
        if request_data["print_type"] == "individual":
            # 개별 평가표 생성
            evaluation_id = request_data["evaluation_ids"][0]
            evaluation_data = await get_evaluation_data(evaluation_id)
            
            print_jobs[job_id]["progress"] = 50
            
            pdf_content = create_individual_evaluation_pdf(
                evaluation_data, 
                request_data.get("template_options", {})
            )
            
            # 파일 저장
            filename = f"evaluation_{evaluation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path = f"outputs/{filename}"
            
            os.makedirs("outputs", exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(pdf_content)
            
        elif request_data["print_type"] == "bulk":
            # 전체 평가표 생성 (ZIP 파일)
            import zipfile
            
            zip_filename = f"evaluations_bulk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            file_path = f"outputs/{zip_filename}"
            
            os.makedirs("outputs", exist_ok=True)
            
            with zipfile.ZipFile(file_path, 'w') as zipf:
                total_evaluations = len(request_data["evaluation_ids"])
                
                for i, evaluation_id in enumerate(request_data["evaluation_ids"]):
                    evaluation_data = await get_evaluation_data(evaluation_id)
                    pdf_content = create_individual_evaluation_pdf(
                        evaluation_data,
                        request_data.get("template_options", {})
                    )
                    
                    company_name = evaluation_data["company"].get("name", "unknown")
                    pdf_filename = f"{company_name}_평가표_{evaluation_id}.pdf"
                    
                    zipf.writestr(pdf_filename, pdf_content)
                    
                    # 진행률 업데이트
                    progress = 20 + int((i + 1) / total_evaluations * 70)
                    print_jobs[job_id]["progress"] = progress
        
        elif request_data["print_type"] == "chairman":
            # 위원장 종합 평가표 생성
            project_id = request_data.get("project_id")
            if not project_id:
                raise ValueError("위원장 평가표 생성에는 프로젝트 ID가 필요합니다")
            
            # 프로젝트 데이터 조회
            project = await db.projects.find_one({"_id": project_id})
            evaluations = await db.evaluations.find({"project_id": project_id}).to_list(length=None)
            
            # 기업 정보 조회
            company_ids = list(set([eval.get("company_id") for eval in evaluations]))
            companies = {}
            for company_id in company_ids:
                company = await db.companies.find_one({"_id": company_id})
                if company:
                    companies[company_id] = company
            
            project_data = {
                "project": project,
                "evaluations": evaluations,
                "companies": companies
            }
            
            print_jobs[job_id]["progress"] = 50
            
            pdf_content = create_chairman_summary_pdf(
                project_data,
                request_data.get("template_options", {})
            )
            
            # 파일 저장
            filename = f"chairman_summary_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path = f"outputs/{filename}"
            
            os.makedirs("outputs", exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(pdf_content)
        
        # 작업 완료
        print_jobs[job_id]["status"] = "completed"
        print_jobs[job_id]["progress"] = 100
        print_jobs[job_id]["file_path"] = file_path
        print_jobs[job_id]["completed_at"] = datetime.utcnow()
        
        logger.info(f"출력 작업 완료: {job_id}", extra={
            'user_id': user.id,
            'job_id': job_id,
            'print_type': request_data["print_type"]
        })
        
    except Exception as e:
        print_jobs[job_id]["status"] = "failed"
        print_jobs[job_id]["error_message"] = str(e)
        logger.error(f"출력 작업 실패: {job_id}, 오류: {e}")

@evaluation_print_router.post("/print-request")
async def create_print_job(
    request_data: EvaluationPrintRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """평가표 출력 작업 생성"""
    try:
        # 권한 확인
        if current_user.role not in ["admin", "secretary", "evaluator"]:
            raise HTTPException(status_code=403, detail="평가표 출력 권한이 없습니다")
        
        # 작업 ID 생성
        job_id = str(uuid.uuid4())
        
        # 작업 상태 초기화
        print_jobs[job_id] = PrintJobStatus(
            job_id=job_id,
            status="pending",
            created_at=datetime.utcnow()
        ).dict()
        
        # 백그라운드 작업 시작
        background_tasks.add_task(
            process_print_job,
            job_id,
            request_data.dict(),
            current_user
        )
        
        logger.info(f"출력 작업 생성: {job_id}", extra={
            'user_id': current_user.id,
            'print_type': request_data.print_type,
            'evaluation_count': len(request_data.evaluation_ids)
        })
        
        return {
            "success": True,
            "job_id": job_id,
            "message": "출력 작업이 시작되었습니다"
        }
        
    except Exception as e:
        logger.error(f"출력 작업 생성 오류: {e}")
        raise HTTPException(status_code=500, detail="출력 작업 생성 중 오류가 발생했습니다")

@evaluation_print_router.get("/print-status/{job_id}")
async def get_print_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """출력 작업 상태 조회"""
    try:
        if job_id not in print_jobs:
            raise HTTPException(status_code=404, detail="출력 작업을 찾을 수 없습니다")
        
        job_status = print_jobs[job_id]
        
        return {
            "success": True,
            "job_status": job_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"출력 작업 상태 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="출력 작업 상태 조회 중 오류가 발생했습니다")

@evaluation_print_router.get("/download/{job_id}")
async def download_print_result(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """출력 결과 다운로드"""
    try:
        if job_id not in print_jobs:
            raise HTTPException(status_code=404, detail="출력 작업을 찾을 수 없습니다")
        
        job_status = print_jobs[job_id]
        
        if job_status["status"] != "completed":
            raise HTTPException(status_code=400, detail="출력 작업이 완료되지 않았습니다")
        
        file_path = job_status["file_path"]
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="출력 파일을 찾을 수 없습니다")
        
        # 파일 이름 추출
        filename = os.path.basename(file_path)
        
        # 파일 다운로드 응답
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"출력 결과 다운로드 오류: {e}")
        raise HTTPException(status_code=500, detail="출력 결과 다운로드 중 오류가 발생했습니다")

@evaluation_print_router.post("/chairman-summary")
async def create_chairman_summary(
    request_data: ChairmanSummaryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """위원장 종합 평가표 생성"""
    try:
        # 권한 확인 (관리자 또는 간사만)
        if current_user.role not in ["admin", "secretary"]:
            raise HTTPException(status_code=403, detail="위원장 평가표 생성 권한이 없습니다")
        
        # 작업 ID 생성
        job_id = str(uuid.uuid4())
        
        # 작업 상태 초기화
        print_jobs[job_id] = PrintJobStatus(
            job_id=job_id,
            status="pending",
            created_at=datetime.utcnow()
        ).dict()
        
        # 요청 데이터에 프로젝트 ID 추가
        request_dict = request_data.dict()
        request_dict["print_type"] = "chairman"
        request_dict["evaluation_ids"] = request_data.evaluation_ids or []
        
        # 백그라운드 작업 시작
        background_tasks.add_task(
            process_print_job,
            job_id,
            request_dict,
            current_user
        )
        
        logger.info(f"위원장 평가표 생성 작업: {job_id}", extra={
            'user_id': current_user.id,
            'project_id': request_data.project_id
        })
        
        return {
            "success": True,
            "job_id": job_id,
            "message": "위원장 종합 평가표 생성 작업이 시작되었습니다"
        }
        
    except Exception as e:
        logger.error(f"위원장 평가표 생성 오류: {e}")
        raise HTTPException(status_code=500, detail="위원장 평가표 생성 중 오류가 발생했습니다")

@evaluation_print_router.get("/jobs")
async def get_print_jobs(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, le=100),
    status: Optional[str] = Query(None)
):
    """출력 작업 목록 조회"""
    try:
        # 권한 확인
        if current_user.role not in ["admin", "secretary"]:
            raise HTTPException(status_code=403, detail="출력 작업 목록 조회 권한이 없습니다")
        
        # 작업 목록 필터링
        jobs = []
        for job_data in print_jobs.values():
            if status and job_data["status"] != status:
                continue
            jobs.append(job_data)
        
        # 생성일 기준 내림차순 정렬
        jobs.sort(key=lambda x: x["created_at"], reverse=True)
        
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
        logger.error(f"출력 작업 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="출력 작업 목록 조회 중 오류가 발생했습니다")