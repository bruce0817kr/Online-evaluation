"""
AI 서비스 모듈
중소기업 지원사업 평가 시스템을 위한 AI 기능들을 제공합니다.
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from pathlib import Path

# AI 모델 라이브러리들
try:
    import openai
    from anthropic import AsyncAnthropic
    HAS_OPENAI = True
    HAS_ANTHROPIC = True
except ImportError:
    HAS_OPENAI = False
    HAS_ANTHROPIC = False
    print("⚠️ AI 라이브러리가 설치되지 않았습니다. pip install openai anthropic 를 실행하세요.")

# 텍스트 처리용
import re
from collections import Counter
import math

logger = logging.getLogger(__name__)

class AIEvaluationService:
    """AI 기반 평가 지원 서비스"""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        
        # API 키 설정
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        
        if openai_key and HAS_OPENAI:
            openai.api_key = openai_key
            self.openai_client = openai.AsyncOpenAI(api_key=openai_key)
            
        if anthropic_key and HAS_ANTHROPIC:
            self.anthropic_client = AsyncAnthropic(api_key=anthropic_key)
            
        # 평가 기준 템플릿들
        self.evaluation_templates = {
            "digital_transformation": {
                "name": "디지털 전환 사업 평가",
                "criteria": [
                    "기술 혁신성과 차별성",
                    "사업 계획의 구체성과 실현가능성",
                    "시장성과 사업화 가능성",
                    "추진 역량과 전문성"
                ],
                "keywords": ["AI", "IoT", "빅데이터", "클라우드", "자동화", "디지털화", "4차산업혁명"]
            },
            "smart_factory": {
                "name": "스마트팩토리 구축 평가",
                "criteria": [
                    "현황 분석의 정확성",
                    "스마트팩토리 기술 적용 계획",
                    "투자 대비 효과성",
                    "구축 및 운영 계획의 실현가능성"
                ],
                "keywords": ["스마트팩토리", "자동화", "센서", "데이터수집", "MES", "ERP", "생산성", "품질관리"]
            }
        }
    
    async def analyze_document_content(self, document_text: str, document_type: str = "business_plan") -> Dict[str, Any]:
        """문서 내용 AI 분석"""
        try:
            if not self.openai_client:
                return self._fallback_document_analysis(document_text)
            
            prompt = f"""
다음은 중소기업 지원사업 신청을 위한 {document_type} 문서입니다.
이 문서를 분석하여 다음 항목들을 평가해주세요:

1. 사업 계획의 구체성 (1-10점)
2. 기술적 실현가능성 (1-10점)  
3. 시장 분석의 적정성 (1-10점)
4. 예산 계획의 합리성 (1-10점)
5. 혁신성과 차별성 (1-10점)

또한 다음 정보를 추출해주세요:
- 주요 키워드 (최대 10개)
- 강점 (3개)
- 개선이 필요한 부분 (3개)
- 전체적인 평가 요약 (2-3문장)

문서 내용:
{document_text[:4000]}  # 토큰 제한을 위해 4000자로 제한

응답은 JSON 형태로 해주세요.
"""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 중소기업 지원사업 전문 평가위원입니다. 공정하고 객관적인 분석을 제공해주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            result_text = response.choices[0].message.content
            
            # JSON 파싱 시도
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                # JSON 파싱 실패시 텍스트 분석으로 대체
                result = self._parse_ai_response_text(result_text)
            
            result["ai_provider"] = "openai"
            result["analyzed_at"] = datetime.utcnow().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"AI 문서 분석 오류: {e}")
            return self._fallback_document_analysis(document_text)
    
    async def suggest_evaluation_scores(self, document_analysis: Dict[str, Any], template_type: str = "digital_transformation") -> Dict[str, Any]:
        """AI 기반 평가 점수 제안"""
        try:
            template = self.evaluation_templates.get(template_type, self.evaluation_templates["digital_transformation"])
            
            if not self.anthropic_client:
                return self._fallback_score_suggestion(document_analysis, template)
            
            prompt = f"""
다음은 문서 분석 결과입니다:
{json.dumps(document_analysis, ensure_ascii=False, indent=2)}

이 분석을 바탕으로 '{template['name']}'의 다음 평가 기준에 대해 점수를 제안해주세요:

평가 기준:
{chr(10).join([f"{i+1}. {criterion}" for i, criterion in enumerate(template['criteria'])])}

각 기준에 대해:
- 점수 (1-25점)
- 근거 (2-3문장)
- 개선 제안 (1-2문장)

전체적인 종합 의견도 함께 제공해주세요.

응답은 JSON 형태로 해주세요.
"""

            response = await self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                temperature=0.2,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            result_text = response.content[0].text
            
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                result = self._parse_score_response_text(result_text, template)
            
            result["ai_provider"] = "anthropic"
            result["template_type"] = template_type
            result["suggested_at"] = datetime.utcnow().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"AI 점수 제안 오류: {e}")
            return self._fallback_score_suggestion(document_analysis, template)
    
    async def detect_plagiarism_similarity(self, document_text: str, existing_documents: List[str]) -> Dict[str, Any]:
        """표절 및 유사도 검사"""
        try:
            # 간단한 텍스트 유사도 분석 (TF-IDF 기반)
            similarities = []
            
            for i, existing_doc in enumerate(existing_documents):
                similarity = self._calculate_text_similarity(document_text, existing_doc)
                if similarity > 0.3:  # 30% 이상 유사도
                    similarities.append({
                        "document_index": i,
                        "similarity_score": similarity,
                        "risk_level": "high" if similarity > 0.7 else "medium" if similarity > 0.5 else "low"
                    })
            
            result = {
                "total_documents_checked": len(existing_documents),
                "similar_documents_found": len(similarities),
                "max_similarity": max([s["similarity_score"] for s in similarities]) if similarities else 0,
                "similarities": similarities,
                "overall_risk": "high" if any(s["similarity_score"] > 0.7 for s in similarities) else "low",
                "checked_at": datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"유사도 검사 오류: {e}")
            return {
                "total_documents_checked": len(existing_documents),
                "similar_documents_found": 0,
                "max_similarity": 0,
                "similarities": [],
                "overall_risk": "unknown",
                "error": str(e),
                "checked_at": datetime.utcnow().isoformat()
            }
    
    async def extract_key_information(self, document_text: str) -> Dict[str, Any]:
        """문서에서 핵심 정보 추출"""
        try:
            # 정규표현식을 사용한 기본 정보 추출
            extracted_info = {
                "company_info": self._extract_company_info(document_text),
                "financial_info": self._extract_financial_info(document_text),
                "technical_info": self._extract_technical_keywords(document_text),
                "project_timeline": self._extract_timeline_info(document_text),
                "extracted_at": datetime.utcnow().isoformat()
            }
            
            # AI를 통한 추가 정보 추출 (가능한 경우)
            if self.openai_client:
                ai_extraction = await self._ai_extract_information(document_text)
                extracted_info.update(ai_extraction)
            
            return extracted_info
            
        except Exception as e:
            logger.error(f"정보 추출 오류: {e}")
            return {"error": str(e), "extracted_at": datetime.utcnow().isoformat()}
    
    def _fallback_document_analysis(self, document_text: str) -> Dict[str, Any]:
        """AI 서비스 없이 기본 문서 분석"""
        # 간단한 텍스트 분석
        word_count = len(document_text.split())
        
        # 키워드 기반 점수 계산
        innovation_keywords = ["혁신", "AI", "인공지능", "자동화", "디지털", "신기술"]
        feasibility_keywords = ["계획", "단계", "일정", "예산", "인력"]
        market_keywords = ["시장", "고객", "수요", "경쟁", "매출"]
        
        innovation_score = min(10, len([k for k in innovation_keywords if k in document_text]) * 2)
        feasibility_score = min(10, len([k for k in feasibility_keywords if k in document_text]) * 2)
        market_score = min(10, len([k for k in market_keywords if k in document_text]) * 2)
        
        return {
            "structure_score": min(10, word_count // 100),  # 글자 수 기반
            "innovation_score": innovation_score,
            "feasibility_score": feasibility_score,
            "market_score": market_score,
            "budget_score": 6,  # 기본값
            "keywords": self._extract_technical_keywords(document_text),
            "strengths": ["문서가 제출되었습니다", "내용이 포함되어 있습니다"],
            "improvements": ["더 구체적인 계획이 필요합니다", "시장 분석을 보완해주세요"],
            "summary": "기본 텍스트 분석이 수행되었습니다. AI 분석을 위해서는 API 키 설정이 필요합니다.",
            "ai_provider": "fallback",
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """두 텍스트 간의 유사도 계산 (코사인 유사도 기반)"""
        try:
            # 간단한 단어 빈도 기반 유사도
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            if len(union) == 0:
                return 0.0
            
            return len(intersection) / len(union)
            
        except:
            return 0.0
    
    def _extract_company_info(self, text: str) -> Dict[str, Any]:
        """회사 정보 추출"""
        company_patterns = [
            r'(주식회사|㈜|유한회사|협동조합)\s*([가-힣\w]+)',
            r'([가-힣\w]+)\s*(주식회사|㈜|유한회사)',
            r'사업자등록번호[:\s]*(\d{3}-\d{2}-\d{5})',
            r'대표자[:\s]*([가-힣]{2,4})'
        ]
        
        extracted = {}
        for pattern in company_patterns:
            matches = re.findall(pattern, text)
            if matches:
                extracted[f"pattern_{len(extracted)}"] = matches[0]
        
        return extracted
    
    def _extract_financial_info(self, text: str) -> Dict[str, Any]:
        """재무 정보 추출"""
        financial_patterns = [
            r'(\d+)\s*억\s*원',
            r'(\d+)\s*만\s*원',
            r'매출[:\s]*(\d+)',
            r'자본금[:\s]*(\d+)'
        ]
        
        extracted = {}
        for pattern in financial_patterns:
            matches = re.findall(pattern, text)
            if matches:
                extracted[f"amount_{len(extracted)}"] = matches[0]
        
        return extracted
    
    def _extract_technical_keywords(self, text: str) -> List[str]:
        """기술 키워드 추출"""
        tech_keywords = [
            "AI", "인공지능", "머신러닝", "딥러닝", "IoT", "사물인터넷",
            "빅데이터", "클라우드", "자동화", "로봇", "센서", "블록체인",
            "VR", "AR", "드론", "3D프린팅", "스마트팩토리", "디지털트윈"
        ]
        
        found_keywords = []
        for keyword in tech_keywords:
            if keyword.lower() in text.lower():
                found_keywords.append(keyword)
        
        return found_keywords[:10]  # 최대 10개
    
    def _extract_timeline_info(self, text: str) -> Dict[str, Any]:
        """일정 정보 추출"""
        timeline_patterns = [
            r'(\d{4})년\s*(\d{1,2})월',
            r'(\d{1,2})개월',
            r'(\d{1,2})년\s*이내'
        ]
        
        extracted = {}
        for pattern in timeline_patterns:
            matches = re.findall(pattern, text)
            if matches:
                extracted[f"timeline_{len(extracted)}"] = matches[0]
        
        return extracted
    
    async def _ai_extract_information(self, document_text: str) -> Dict[str, Any]:
        """AI를 통한 추가 정보 추출"""
        try:
            prompt = f"""
다음 문서에서 핵심 정보를 추출해주세요:

1. 회사명
2. 대표자명  
3. 사업 분야
4. 주요 기술
5. 예상 투자액
6. 프로젝트 기간
7. 기대 효과

문서: {document_text[:2000]}

JSON 형태로 응답해주세요.
"""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=800
            )
            
            result_text = response.choices[0].message.content
            
            try:
                return json.loads(result_text)
            except:
                return {"ai_extraction": result_text}
                
        except Exception as e:
            logger.error(f"AI 정보 추출 오류: {e}")
            return {}

# AI 서비스 인스턴스
ai_service = AIEvaluationService()