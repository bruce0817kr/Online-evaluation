"""
향상된 AI 서비스 모듈
데이터베이스 기반 AI 공급자 관리 및 다중 공급자 지원
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from pathlib import Path
import base64
from cryptography.fernet import Fernet
from motor.motor_asyncio import AsyncIOMotorClient

# AI 모델 라이브러리들
try:
    import openai
    from anthropic import AsyncAnthropic
    import google.generativeai as genai
    HAS_OPENAI = True
    HAS_ANTHROPIC = True
    HAS_GOOGLE = True
except ImportError as e:
    HAS_OPENAI = False
    HAS_ANTHROPIC = False
    HAS_GOOGLE = False
    print(f"⚠️ AI 라이브러리가 설치되지 않았습니다: {e}")

# 텍스트 처리용
import re
from collections import Counter
import math

logger = logging.getLogger(__name__)

class EnhancedAIService:
    """향상된 AI 기반 평가 지원 서비스"""
    
    def __init__(self, db_client: AsyncIOMotorClient = None):
        self.db = None
        self.ai_providers_collection = None
        self.ai_models_collection = None
        self.ai_jobs_collection = None
        
        # 암호화 설정
        self.encryption_key = os.getenv("AI_CONFIG_ENCRYPTION_KEY")
        if self.encryption_key:
            self.cipher_suite = Fernet(self.encryption_key.encode() if isinstance(self.encryption_key, str) else self.encryption_key)
        else:
            self.cipher_suite = None
            logger.warning("AI_CONFIG_ENCRYPTION_KEY가 설정되지 않았습니다. API 키 암호화가 비활성화됩니다.")
        
        # 활성화된 AI 클라이언트들
        self.active_clients = {}
        self.provider_configs = {}
        
        # 데이터베이스 연결 설정
        if db_client:
            self._setup_database(db_client)
        
        # 평가 기준 템플릿들 (향상된 버전)
        self.evaluation_templates = {
            "digital_transformation": {
                "name": "디지털 전환 사업 평가",
                "criteria": [
                    {"name": "기술 혁신성과 차별성", "max_score": 25, "weight": 0.3},
                    {"name": "사업 계획의 구체성과 실현가능성", "max_score": 25, "weight": 0.25},
                    {"name": "시장성과 사업화 가능성", "max_score": 25, "weight": 0.25},
                    {"name": "추진 역량과 전문성", "max_score": 25, "weight": 0.2}
                ],
                "keywords": ["AI", "IoT", "빅데이터", "클라우드", "자동화", "디지털화", "4차산업혁명"],
                "bonus_criteria": ["특허 보유", "정부 인증", "수출 경험"]
            },
            "smart_factory": {
                "name": "스마트팩토리 구축 평가",
                "criteria": [
                    {"name": "현황 분석의 정확성", "max_score": 20, "weight": 0.2},
                    {"name": "스마트팩토리 기술 적용 계획", "max_score": 30, "weight": 0.3},
                    {"name": "투자 대비 효과성", "max_score": 25, "weight": 0.25},
                    {"name": "구축 및 운영 계획의 실현가능성", "max_score": 25, "weight": 0.25}
                ],
                "keywords": ["스마트팩토리", "자동화", "센서", "데이터수집", "MES", "ERP", "생산성", "품질관리"],
                "bonus_criteria": ["ISO 인증", "스마트공장 수준 진단", "컨설팅 이력"]
            },
            "r_and_d": {
                "name": "R&D 과제 평가",
                "criteria": [
                    {"name": "기술적 우수성", "max_score": 30, "weight": 0.3},
                    {"name": "연구개발 계획의 적정성", "max_score": 25, "weight": 0.25},
                    {"name": "연구개발 역량", "max_score": 25, "weight": 0.25},
                    {"name": "활용 및 사업화 계획", "max_score": 20, "weight": 0.2}
                ],
                "keywords": ["연구개발", "R&D", "기술개발", "특허", "논문", "프로토타입", "시제품"],
                "bonus_criteria": ["박사급 연구인력", "연구장비 보유", "산학협력"]
            }
        }
    
    def _setup_database(self, db_client: AsyncIOMotorClient):
        """데이터베이스 연결 설정"""
        self.db = db_client.online_evaluation
        self.ai_providers_collection = self.db.ai_providers
        self.ai_models_collection = self.db.ai_models
        self.ai_jobs_collection = self.db.ai_analysis_jobs
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """API 키 복호화"""
        if not self.cipher_suite:
            return encrypted_key  # 암호화되지 않은 경우 그대로 반환
        
        try:
            return self.cipher_suite.decrypt(base64.b64decode(encrypted_key.encode())).decode()
        except Exception as e:
            logger.error(f"API 키 복호화 실패: {e}")
            return ""
    
    async def load_ai_providers(self):
        """데이터베이스에서 AI 공급자 설정 로드"""
        if not self.ai_providers_collection:
            logger.warning("데이터베이스가 연결되지 않았습니다. 환경변수 기반으로 동작합니다.")
            await self._fallback_to_env_config()
            return
        
        try:
            # 활성화된 공급자들만 조회 (우선순위 순으로 정렬)
            providers = await self.ai_providers_collection.find(
                {"is_active": True}
            ).sort("priority", 1).to_list(length=None)
            
            self.active_clients = {}
            self.provider_configs = {}
            
            for provider in providers:
                provider_name = provider["provider_name"]
                api_key = self.decrypt_api_key(provider["api_key"])
                
                if not api_key:
                    logger.warning(f"AI 공급자 {provider_name}의 API 키를 복호화할 수 없습니다.")
                    continue
                
                # 공급자별 클라이언트 생성
                client = await self._create_ai_client(provider_name, api_key, provider.get("api_endpoint"))
                
                if client:
                    self.active_clients[provider_name] = client
                    self.provider_configs[provider_name] = {
                        "id": str(provider["_id"]),
                        "display_name": provider["display_name"],
                        "max_tokens": provider.get("max_tokens", 4096),
                        "temperature": provider.get("temperature", 0.3),
                        "priority": provider["priority"]
                    }
                    
                    logger.info(f"AI 공급자 로드 성공: {provider_name}")
            
            logger.info(f"총 {len(self.active_clients)}개의 AI 공급자가 로드되었습니다.")
            
        except Exception as e:
            logger.error(f"AI 공급자 로드 오류: {e}")
            await self._fallback_to_env_config()
    
    async def _create_ai_client(self, provider_name: str, api_key: str, api_endpoint: Optional[str] = None):
        """AI 공급자별 클라이언트 생성"""
        try:
            # OpenAI (ChatGPT) 모델들
            if provider_name == "openai" and HAS_OPENAI:
                return openai.AsyncOpenAI(api_key=api_key)
                
            # Anthropic Claude 모델들
            elif provider_name == "anthropic" and HAS_ANTHROPIC:
                return AsyncAnthropic(api_key=api_key)
                
            # Google Gemini 모델들
            elif provider_name == "google" and HAS_GOOGLE:
                genai.configure(api_key=api_key)
                return genai.GenerativeModel('gemini-pro')
                
            # Groq (Llama, Mixtral 등)
            elif provider_name == "groq" and HAS_OPENAI:
                return openai.AsyncOpenAI(
                    api_key=api_key,
                    base_url="https://api.groq.com/openai/v1"
                )
            
            # DeepSeek 모델들
            elif provider_name == "deepseek" and HAS_OPENAI:
                return openai.AsyncOpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com/v1"
                )
            
            # MiniMax 모델들
            elif provider_name == "minimax" and HAS_OPENAI:
                # MiniMax는 자체 API 구조를 사용하지만 OpenAI 호환 형식도 지원
                return openai.AsyncOpenAI(
                    api_key=api_key,
                    base_url=api_endpoint or "https://api.minimax.chat/v1"
                )
            
            # Cohere 모델들
            elif provider_name == "cohere" and HAS_OPENAI:
                return openai.AsyncOpenAI(
                    api_key=api_key,
                    base_url="https://api.cohere.ai/v1"
                )
            
            # Together AI (다양한 오픈소스 모델 제공)
            elif provider_name == "together" and HAS_OPENAI:
                return openai.AsyncOpenAI(
                    api_key=api_key,
                    base_url="https://api.together.xyz/v1"
                )
            
            # Perplexity AI
            elif provider_name == "perplexity" and HAS_OPENAI:
                return openai.AsyncOpenAI(
                    api_key=api_key,
                    base_url="https://api.perplexity.ai"
                )
            
            # Mistral AI
            elif provider_name == "mistral" and HAS_OPENAI:
                return openai.AsyncOpenAI(
                    api_key=api_key,
                    base_url="https://api.mistral.ai/v1"
                )
            
            # 커스텀 엔드포인트 (자체 호스팅 모델 등)
            elif provider_name == "custom" and HAS_OPENAI and api_endpoint:
                return openai.AsyncOpenAI(
                    api_key=api_key,
                    base_url=api_endpoint
                )
            
            else:
                logger.warning(f"지원하지 않는 AI 공급자이거나 라이브러리가 없습니다: {provider_name}")
                return None
                
        except Exception as e:
            logger.error(f"AI 클라이언트 생성 오류 ({provider_name}): {e}")
            return None
    
    async def _fallback_to_env_config(self):
        """환경변수 기반 폴백 설정"""
        logger.info("환경변수 기반 AI 설정으로 폴백합니다.")
        
        # OpenAI 설정
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and HAS_OPENAI:
            self.active_clients["openai"] = openai.AsyncOpenAI(api_key=openai_key)
            self.provider_configs["openai"] = {
                "display_name": "OpenAI ChatGPT",
                "max_tokens": 4096,
                "temperature": 0.3,
                "priority": 1
            }
        
        # Anthropic 설정
        anthropic_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        if anthropic_key and HAS_ANTHROPIC:
            self.active_clients["anthropic"] = AsyncAnthropic(api_key=anthropic_key)
            self.provider_configs["anthropic"] = {
                "display_name": "Anthropic Claude",
                "max_tokens": 4096,
                "temperature": 0.3,
                "priority": 2
            }
        
        # Groq 설정
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and HAS_OPENAI:
            self.active_clients["groq"] = openai.AsyncOpenAI(
                api_key=groq_key,
                base_url="https://api.groq.com/openai/v1"
            )
            self.provider_configs["groq"] = {
                "display_name": "Groq (Llama3)",
                "max_tokens": 8192,
                "temperature": 0.3,
                "priority": 3
            }
        
        # DeepSeek 설정
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_key and HAS_OPENAI:
            self.active_clients["deepseek"] = openai.AsyncOpenAI(
                api_key=deepseek_key,
                base_url="https://api.deepseek.com/v1"
            )
            self.provider_configs["deepseek"] = {
                "display_name": "DeepSeek",
                "max_tokens": 4096,
                "temperature": 0.3,
                "priority": 4
            }
        
        # MiniMax 설정
        minimax_key = os.getenv("MINIMAX_API_KEY")
        if minimax_key and HAS_OPENAI:
            self.active_clients["minimax"] = openai.AsyncOpenAI(
                api_key=minimax_key,
                base_url="https://api.minimax.chat/v1"
            )
            self.provider_configs["minimax"] = {
                "display_name": "MiniMax",
                "max_tokens": 1000000,  # 1M 토큰 컨텍스트
                "temperature": 0.3,
                "priority": 5
            }
    
    def get_primary_provider(self) -> Optional[str]:
        """우선순위가 가장 높은 공급자 반환"""
        if not self.provider_configs:
            return None
        
        return min(self.provider_configs.keys(), key=lambda k: self.provider_configs[k]["priority"])
    
    async def analyze_document_content(self, document_text: str, document_type: str = "business_plan") -> Dict[str, Any]:
        """문서 내용 AI 분석 (다중 공급자 지원)"""
        # AI 공급자 설정이 로드되지 않은 경우 로드
        if not self.active_clients:
            await self.load_ai_providers()
        
        # 사용할 공급자 선택 (우선순위 순)
        provider_name = self.get_primary_provider()
        
        if not provider_name or provider_name not in self.active_clients:
            return self._fallback_document_analysis(document_text)
        
        try:
            client = self.active_clients[provider_name]
            config = self.provider_configs[provider_name]
            
            # 공급자별 분석 실행
            if provider_name == "openai":
                result = await self._analyze_with_openai(client, document_text, document_type, config)
            elif provider_name == "anthropic":
                result = await self._analyze_with_anthropic(client, document_text, document_type, config)
            elif provider_name == "google":
                result = await self._analyze_with_google(client, document_text, document_type, config)
            elif provider_name == "groq":
                result = await self._analyze_with_groq(client, document_text, document_type, config)
            elif provider_name == "deepseek":
                result = await self._analyze_with_deepseek(client, document_text, document_type, config)
            elif provider_name == "minimax":
                result = await self._analyze_with_minimax(client, document_text, document_type, config)
            elif provider_name in ["together", "perplexity", "mistral", "cohere", "custom"]:
                result = await self._analyze_with_openai_compatible(client, document_text, document_type, config, provider_name)
            else:
                result = self._fallback_document_analysis(document_text)
            
            result["ai_provider"] = provider_name
            result["analyzed_at"] = datetime.utcnow().isoformat()
            
            # 분석 작업 기록 저장
            await self._save_analysis_job("document_analysis", {
                "document_type": document_type,
                "text_length": len(document_text)
            }, result, provider_name)
            
            return result
            
        except Exception as e:
            logger.error(f"AI 문서 분석 오류 ({provider_name}): {e}")
            
            # 다른 공급자로 재시도
            for backup_provider in self.active_clients.keys():
                if backup_provider != provider_name:
                    try:
                        logger.info(f"백업 공급자로 재시도: {backup_provider}")
                        return await self._retry_with_provider(backup_provider, document_text, document_type)
                    except Exception as backup_e:
                        logger.error(f"백업 공급자 ({backup_provider}) 실패: {backup_e}")
                        continue
            
            # 모든 공급자 실패시 폴백
            return self._fallback_document_analysis(document_text)
    
    async def _analyze_with_openai(self, client, document_text: str, document_type: str, config: Dict) -> Dict[str, Any]:
        """OpenAI를 사용한 문서 분석"""
        prompt = self._create_analysis_prompt(document_text, document_type)
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 중소기업 지원사업 전문 평가위원입니다. 공정하고 객관적인 분석을 제공해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=config["temperature"],
            max_tokens=min(config["max_tokens"], 1500)
        )
        
        result_text = response.choices[0].message.content
        return self._parse_analysis_response(result_text)
    
    async def _analyze_with_anthropic(self, client, document_text: str, document_type: str, config: Dict) -> Dict[str, Any]:
        """Anthropic Claude를 사용한 문서 분석"""
        prompt = self._create_analysis_prompt(document_text, document_type)
        
        response = await client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=min(config["max_tokens"], 1500),
            temperature=config["temperature"],
            messages=[{"role": "user", "content": prompt}]
        )
        
        result_text = response.content[0].text
        return self._parse_analysis_response(result_text)
    
    async def _analyze_with_google(self, client, document_text: str, document_type: str, config: Dict) -> Dict[str, Any]:
        """Google Gemini를 사용한 문서 분석"""
        prompt = self._create_analysis_prompt(document_text, document_type)
        
        response = client.generate_content(prompt)
        result_text = response.text
        return self._parse_analysis_response(result_text)
    
    async def _analyze_with_groq(self, client, document_text: str, document_type: str, config: Dict) -> Dict[str, Any]:
        """Groq를 사용한 문서 분석 (비용 최적화된 모델 선택)"""
        prompt = self._create_analysis_prompt(document_text, document_type)
        
        # 비용 효율적인 모델 선택
        optimal_model = self._select_optimal_groq_model(
            document_length=len(document_text),
            analysis_type=document_type,
            budget_priority=config.get("budget_priority", "balanced")
        )
        
        response = await client.chat.completions.create(
            model=optimal_model,
            messages=[
                {"role": "system", "content": "당신은 중소기업 지원사업 전문 평가위원입니다. 공정하고 객관적인 분석을 제공해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=config["temperature"],
            max_tokens=min(config["max_tokens"], 1500)
        )
        
        result_text = response.choices[0].message.content
        analysis_result = self._parse_analysis_response(result_text)
        
        # 비용 정보 추가
        analysis_result["model_used"] = optimal_model
        analysis_result["estimated_cost"] = self._calculate_token_cost(prompt + result_text, optimal_model)
        
        return analysis_result
    
    async def _analyze_with_deepseek(self, client, document_text: str, document_type: str, config: Dict) -> Dict[str, Any]:
        """DeepSeek를 사용한 문서 분석"""
        prompt = self._create_analysis_prompt(document_text, document_type)
        
        # DeepSeek 최적 모델 선택
        model = self._select_deepseek_model(len(document_text))
        
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "당신은 중소기업 지원사업 전문 평가위원입니다. 논리적이고 단계별 분석을 제공해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=config["temperature"],
            max_tokens=min(config["max_tokens"], 2000)
        )
        
        result_text = response.choices[0].message.content
        analysis_result = self._parse_analysis_response(result_text)
        analysis_result["model_used"] = model
        return analysis_result
    
    async def _analyze_with_minimax(self, client, document_text: str, document_type: str, config: Dict) -> Dict[str, Any]:
        """MiniMax를 사용한 문서 분석 (초장문 특화)"""
        prompt = self._create_analysis_prompt(document_text, document_type)
        
        # MiniMax 모델 선택
        model = "minimax-text-01" if len(document_text) > 50000 else "minimax-m1-40k"
        
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "당신은 중소기업 지원사업 전문 평가위원입니다. 장문 문서에 대한 포괄적 분석을 제공해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=config["temperature"],
            max_tokens=min(config["max_tokens"], 3000)
        )
        
        result_text = response.choices[0].message.content
        analysis_result = self._parse_analysis_response(result_text)
        analysis_result["model_used"] = model
        return analysis_result
    
    async def _analyze_with_openai_compatible(self, client, document_text: str, document_type: str, config: Dict, provider_name: str) -> Dict[str, Any]:
        """OpenAI 호환 API를 사용하는 다른 공급자들을 위한 통합 분석 함수"""
        prompt = self._create_analysis_prompt(document_text, document_type)
        
        # 공급자별 최적 모델 선택
        model = self._select_provider_model(provider_name, len(document_text))
        
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "당신은 중소기업 지원사업 전문 평가위원입니다. 객관적이고 전문적인 분석을 제공해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=config["temperature"],
            max_tokens=min(config["max_tokens"], 1500)
        )
        
        result_text = response.choices[0].message.content
        analysis_result = self._parse_analysis_response(result_text)
        analysis_result["model_used"] = model
        analysis_result["provider"] = provider_name
        return analysis_result
    
    def _create_analysis_prompt(self, document_text: str, document_type: str) -> str:
        """분석용 프롬프트 생성"""
        return f"""
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
{document_text[:4000]}

응답은 JSON 형태로 해주세요.
"""
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """AI 응답 파싱"""
        try:
            # JSON 파싱 시도
            result = json.loads(response_text)
            
            # 필수 필드 확인 및 기본값 설정
            default_result = {
                "structure_score": 7,
                "innovation_score": 7,
                "feasibility_score": 7,
                "market_score": 7,
                "budget_score": 7,
                "keywords": [],
                "strengths": ["분석이 완료되었습니다"],
                "improvements": ["상세한 검토가 필요합니다"],
                "summary": "AI 분석이 수행되었습니다."
            }
            
            # 결과 병합
            for key, default_value in default_result.items():
                if key not in result:
                    result[key] = default_value
            
            return result
            
        except json.JSONDecodeError:
            # JSON 파싱 실패시 텍스트 기반 파싱
            return self._parse_ai_response_text(response_text)
    
    def _parse_ai_response_text(self, text: str) -> Dict[str, Any]:
        """텍스트 기반 AI 응답 파싱"""
        # 간단한 텍스트 파싱 로직
        lines = text.split('\n')
        
        result = {
            "structure_score": 7,
            "innovation_score": 7,
            "feasibility_score": 7,
            "market_score": 7,
            "budget_score": 7,
            "keywords": self._extract_technical_keywords(text),
            "strengths": ["AI 분석이 완료되었습니다"],
            "improvements": ["추가 검토가 필요합니다"],
            "summary": text[:200] + "..." if len(text) > 200 else text
        }
        
        return result
    
    async def suggest_evaluation_scores(self, document_analysis: Dict[str, Any], template_type: str = "digital_transformation") -> Dict[str, Any]:
        """AI 기반 평가 점수 제안 (다중 공급자 지원)"""
        if not self.active_clients:
            await self.load_ai_providers()
        
        provider_name = self.get_primary_provider()
        
        if not provider_name or provider_name not in self.active_clients:
            return self._fallback_score_suggestion(document_analysis, self.evaluation_templates.get(template_type))
        
        try:
            template = self.evaluation_templates.get(template_type, self.evaluation_templates["digital_transformation"])
            client = self.active_clients[provider_name]
            config = self.provider_configs[provider_name]
            
            prompt = f"""
다음은 문서 분석 결과입니다:
{json.dumps(document_analysis, ensure_ascii=False, indent=2)}

이 분석을 바탕으로 '{template['name']}'의 다음 평가 기준에 대해 점수를 제안해주세요:

평가 기준:
{chr(10).join([f"{i+1}. {criterion['name']} (최대 {criterion['max_score']}점)" for i, criterion in enumerate(template['criteria'])])}

각 기준에 대해:
- 점수 (기준별 최대점수 참고)
- 근거 (2-3문장)
- 개선 제안 (1-2문장)

전체적인 종합 의견도 함께 제공해주세요.

응답은 JSON 형태로 해주세요.
"""

            # 공급자별 점수 제안 실행
            if provider_name in ["openai", "groq"]:
                response = await client.chat.completions.create(
                    model="gpt-4o-mini" if provider_name == "openai" else "llama3-70b-8192",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=config["temperature"],
                    max_tokens=min(config["max_tokens"], 2000)
                )
                result_text = response.choices[0].message.content
                
            elif provider_name == "anthropic":
                response = await client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=min(config["max_tokens"], 2000),
                    temperature=config["temperature"],
                    messages=[{"role": "user", "content": prompt}]
                )
                result_text = response.content[0].text
                
            elif provider_name == "google":
                response = client.generate_content(prompt)
                result_text = response.text
            
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                result = self._parse_score_response_text(result_text, template)
            
            result["ai_provider"] = provider_name
            result["template_type"] = template_type
            result["suggested_at"] = datetime.utcnow().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"AI 점수 제안 오류 ({provider_name}): {e}")
            return self._fallback_score_suggestion(document_analysis, template)
    
    async def _save_analysis_job(self, job_type: str, input_data: Dict, result_data: Dict, provider_used: str):
        """분석 작업 기록 저장"""
        if not self.ai_jobs_collection:
            return
        
        try:
            job_data = {
                "job_type": job_type,
                "input_data": input_data,
                "status": "completed",
                "provider_used": provider_used,
                "result_data": result_data,
                "created_at": datetime.utcnow(),
                "completed_at": datetime.utcnow()
            }
            
            await self.ai_jobs_collection.insert_one(job_data)
            
        except Exception as e:
            logger.error(f"분석 작업 기록 저장 오류: {e}")
    
    # 기존 메소드들도 유지 (하위 호환성)
    async def detect_plagiarism_similarity(self, document_text: str, existing_documents: List[str]) -> Dict[str, Any]:
        """표절 및 유사도 검사"""
        try:
            similarities = []
            
            for i, existing_doc in enumerate(existing_documents):
                similarity = self._calculate_text_similarity(document_text, existing_doc)
                if similarity > 0.3:
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
            extracted_info = {
                "company_info": self._extract_company_info(document_text),
                "financial_info": self._extract_financial_info(document_text),
                "technical_info": self._extract_technical_keywords(document_text),
                "project_timeline": self._extract_timeline_info(document_text),
                "extracted_at": datetime.utcnow().isoformat()
            }
            
            # AI를 통한 추가 정보 추출
            if self.active_clients:
                provider_name = self.get_primary_provider()
                if provider_name:
                    ai_extraction = await self._ai_extract_information(document_text, provider_name)
                    extracted_info.update(ai_extraction)
            
            return extracted_info
            
        except Exception as e:
            logger.error(f"정보 추출 오류: {e}")
            return {"error": str(e), "extracted_at": datetime.utcnow().isoformat()}
    
    # 기존 유틸리티 메소드들 유지
    def _fallback_document_analysis(self, document_text: str) -> Dict[str, Any]:
        """AI 서비스 없이 기본 문서 분석"""
        word_count = len(document_text.split())
        
        innovation_keywords = ["혁신", "AI", "인공지능", "자동화", "디지털", "신기술"]
        feasibility_keywords = ["계획", "단계", "일정", "예산", "인력"]
        market_keywords = ["시장", "고객", "수요", "경쟁", "매출"]
        
        innovation_score = min(10, len([k for k in innovation_keywords if k in document_text]) * 2)
        feasibility_score = min(10, len([k for k in feasibility_keywords if k in document_text]) * 2)
        market_score = min(10, len([k for k in market_keywords if k in document_text]) * 2)
        
        return {
            "structure_score": min(10, word_count // 100),
            "innovation_score": innovation_score,
            "feasibility_score": feasibility_score,
            "market_score": market_score,
            "budget_score": 6,
            "keywords": self._extract_technical_keywords(document_text),
            "strengths": ["문서가 제출되었습니다", "내용이 포함되어 있습니다"],
            "improvements": ["더 구체적인 계획이 필요합니다", "시장 분석을 보완해주세요"],
            "summary": "기본 텍스트 분석이 수행되었습니다. AI 분석을 위해서는 관리자가 AI 공급자를 설정해야 합니다.",
            "ai_provider": "fallback",
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def _fallback_score_suggestion(self, document_analysis: Dict[str, Any], template: Dict) -> Dict[str, Any]:
        """AI 없이 기본 점수 제안"""
        criteria_scores = []
        
        if template and "criteria" in template:
            for criterion in template["criteria"]:
                score = min(criterion["max_score"], 
                           int(criterion["max_score"] * 0.7))  # 기본 70% 점수
                criteria_scores.append({
                    "name": criterion["name"],
                    "suggested_score": score,
                    "max_score": criterion["max_score"],
                    "reasoning": "기본 분석 결과입니다.",
                    "improvement": "상세한 검토가 필요합니다."
                })
        
        return {
            "criteria_scores": criteria_scores,
            "total_score": sum(score["suggested_score"] for score in criteria_scores),
            "overall_comment": "기본 점수 제안입니다. AI 분석을 위해서는 관리자가 AI 공급자를 설정해야 합니다.",
            "ai_provider": "fallback",
            "suggested_at": datetime.utcnow().isoformat()
        }
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """두 텍스트 간의 유사도 계산"""
        try:
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
        
        return found_keywords[:10]
    
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
    
    def _select_optimal_groq_model(self, document_length: int, analysis_type: str, budget_priority: str = "balanced") -> str:
        """비용 효율성을 고려한 최적 Groq 모델 선택"""
        
        # 토큰 수 추정 (문자 수 / 4)
        estimated_tokens = document_length // 4
        
        # 초장문 문서 처리 (50K+ 토큰) - MiniMax 권장하지만 Groq에서는 최대 컨텍스트 모델 사용
        if estimated_tokens > 50000:
            return "mixtral-8x7b-32768"  # 32K 컨텍스트, 긴 문서 처리 가능
        
        # 예산 우선 정책
        if budget_priority == "cost_first":
            if estimated_tokens < 4000:
                return "llama3.1-8b-instant"  # $0.13/1M, 최고 속도
            else:
                return "gemma2-9b-it"  # $0.40/1M, 균형잡힌 성능
        
        # 성능 우선 정책
        elif budget_priority == "performance_first":
            if analysis_type in ["complex_analysis", "scoring", "detailed_evaluation"]:
                return "llama3.3-70b-versatile"  # $1.38/1M, 최고 성능
            else:
                return "qwen-32b-preview"  # $0.88/1M, reasoning 강점
        
        # 균형 정책 (기본값)
        else:
            if analysis_type in ["tool_usage", "step_by_step"]:
                return "qwq-32b-preview"  # $0.68/1M, 툴 사용 최적화
            elif estimated_tokens < 8000:
                return "llama3.1-8b-instant"  # 빠른 처리, 저비용
            elif estimated_tokens < 30000:
                return "qwen-32b-preview"  # 중간 성능+비용, 131K 컨텍스트
            else:
                return "mixtral-8x7b-32768"  # 긴 문서 처리
    
    def _select_deepseek_model(self, document_length: int) -> str:
        """DeepSeek 최적 모델 선택"""
        estimated_tokens = document_length // 4
        
        if estimated_tokens > 100000:
            return "deepseek-chat"  # 긴 컨텍스트
        elif estimated_tokens > 30000:
            return "deepseek-coder"  # 코드/구조화된 분석
        else:
            return "deepseek-chat"  # 기본 모델
    
    def _select_provider_model(self, provider_name: str, document_length: int) -> str:
        """공급자별 최적 모델 선택"""
        estimated_tokens = document_length // 4
        
        models = {
            "together": {
                "small": "meta-llama/Llama-2-7b-chat-hf",
                "medium": "meta-llama/Llama-2-13b-chat-hf", 
                "large": "meta-llama/Llama-2-70b-chat-hf"
            },
            "perplexity": {
                "small": "llama-3.1-sonar-small-128k-online",
                "medium": "llama-3.1-sonar-large-128k-online",
                "large": "llama-3.1-sonar-huge-128k-online"
            },
            "mistral": {
                "small": "mistral-small-latest",
                "medium": "mistral-medium-latest",
                "large": "mistral-large-latest"
            },
            "cohere": {
                "small": "command-light",
                "medium": "command",
                "large": "command-r-plus"
            },
            "custom": {
                "small": "default",
                "medium": "default", 
                "large": "default"
            }
        }
        
        if estimated_tokens < 4000:
            return models.get(provider_name, {}).get("small", "default")
        elif estimated_tokens < 20000:
            return models.get(provider_name, {}).get("medium", "default")
        else:
            return models.get(provider_name, {}).get("large", "default")
    
    def _calculate_token_cost(self, text: str, model: str) -> Dict[str, float]:
        """모델별 토큰 비용 계산"""
        
        # 토큰 수 추정 (문자 수 / 4)
        estimated_tokens = len(text) // 4
        tokens_in_millions = estimated_tokens / 1_000_000
        
        # 모델별 비용 정보 (blended 가격 기준, $/1M 토큰)
        model_costs = {
            # Groq 모델들
            "llama3.1-8b-instant": 0.13,
            "llama3.3-70b-versatile": 1.38,
            "qwen-32b-preview": 0.88,
            "qwq-32b-preview": 0.68,
            "gemma2-9b-it": 0.40,
            "deepseek-r1-distill-llama-70b": 1.74,
            "mixtral-8x7b-32768": 0.24,
            
            # OpenAI ChatGPT 모델들
            "gpt-4o": 5.00,
            "gpt-4o-mini": 0.60,
            "gpt-4-turbo": 15.00,
            "gpt-4": 30.00,
            "gpt-3.5-turbo": 1.00,
            "gpt-3.5-turbo-16k": 3.00,
            
            # DeepSeek 모델들
            "deepseek-chat": 0.27,
            "deepseek-coder": 0.27,
            "deepseek-v2.5": 0.55,
            
            # MiniMax 모델들
            "minimax-text-01": 0.42,
            "minimax-m1-40k": 0.82,
            
            # Anthropic Claude 모델들
            "claude-3-5-sonnet-20241022": 3.00,
            "claude-3-5-haiku-20241022": 1.00,
            "claude-3-opus-20240229": 15.00,
            
            # Google Gemini 모델들
            "gemini-1.5-pro": 3.50,
            "gemini-1.5-flash": 0.35,
            "gemini-pro": 0.50,
            
            # Together AI 모델들
            "meta-llama/Llama-2-7b-chat-hf": 0.20,
            "meta-llama/Llama-2-13b-chat-hf": 0.22,
            "meta-llama/Llama-2-70b-chat-hf": 0.90,
            
            # Perplexity 모델들
            "llama-3.1-sonar-small-128k-online": 0.20,
            "llama-3.1-sonar-large-128k-online": 1.00,
            "llama-3.1-sonar-huge-128k-online": 5.00,
            
            # Mistral 모델들
            "mistral-small-latest": 1.00,
            "mistral-medium-latest": 2.70,
            "mistral-large-latest": 4.00,
            
            # Cohere 모델들
            "command-light": 0.30,
            "command": 1.00,
            "command-r-plus": 3.00,
            
            # 기타/커스텀 모델들
            "default": 1.00
        }
        
        cost_per_million = model_costs.get(model, 0.50)  # 기본값
        estimated_cost = tokens_in_millions * cost_per_million
        
        return {
            "estimated_tokens": estimated_tokens,
            "cost_per_million_tokens": cost_per_million,
            "estimated_cost_usd": round(estimated_cost, 4),
            "estimated_cost_krw": round(estimated_cost * 1300, 2)  # USD to KRW 환율 적용
        }
    
    def get_cost_optimization_stats(self) -> Dict[str, Any]:
        """비용 최적화 통계 반환"""
        return {
            "available_models": {
                "groq": [
                    {
                        "name": "llama3.1-8b-instant",
                        "cost_per_1m": 0.13,
                        "speed_tps": "750-1250",
                        "best_for": "실시간 처리, 대량 분석"
                    },
                    {
                        "name": "qwq-32b-preview", 
                        "cost_per_1m": 0.68,
                        "speed_tps": "400",
                        "best_for": "툴 사용, 단계별 분석"
                    },
                    {
                        "name": "llama3.3-70b-versatile",
                        "cost_per_1m": 1.38,
                        "speed_tps": "275-330", 
                        "best_for": "고정확도 평가, 복잡 분석"
                    }
                ],
                "minimax": [
                    {
                        "name": "minimax-text-01",
                        "cost_per_1m": 0.42,
                        "speed_tps": "34",
                        "best_for": "초장문 문서 (1M 토큰)"
                    }
                ]
            },
            "cost_comparison": {
                "1000_evaluations_per_month": {
                    "quick_review_2k_tokens": "$0.26 (llama3.1-8b)",
                    "standard_eval_5k_tokens": "$3.40 (qwq-32b)",
                    "detailed_analysis_8k_tokens": "$11.04 (llama3.3-70b)",
                    "long_document_20k_tokens": "$8.40 (minimax-text-01)"
                }
            },
            "optimization_tips": [
                "문서 길이가 4K 토큰 이하면 llama3.1-8b 사용 권장",
                "복잡한 평가는 qwq-32b로 균형잡힌 성능 확보",
                "최고 정확도가 필요할 때만 llama3.3-70b 사용",
                "50K+ 토큰 문서는 MiniMax나 Mixtral 모델 사용"
            ]
        }
    
    async def _ai_extract_information(self, document_text: str, provider_name: str) -> Dict[str, Any]:
        """AI를 통한 추가 정보 추출"""
        try:
            client = self.active_clients[provider_name]
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

            if provider_name in ["openai", "groq"]:
                response = await client.chat.completions.create(
                    model="gpt-4o-mini" if provider_name == "openai" else "llama3-8b-8192",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=800
                )
                result_text = response.choices[0].message.content
                
            elif provider_name == "anthropic":
                response = await client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=800,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )
                result_text = response.content[0].text
                
            elif provider_name == "google":
                response = client.generate_content(prompt)
                result_text = response.text
            
            try:
                return json.loads(result_text)
            except:
                return {"ai_extraction": result_text}
                
        except Exception as e:
            logger.error(f"AI 정보 추출 오류: {e}")
            return {}
    
    def _parse_score_response_text(self, text: str, template: Dict) -> Dict[str, Any]:
        """점수 응답 텍스트 파싱"""
        criteria_scores = []
        
        if template and "criteria" in template:
            for criterion in template["criteria"]:
                score = min(criterion["max_score"], 
                           int(criterion["max_score"] * 0.75))
                criteria_scores.append({
                    "name": criterion["name"],
                    "suggested_score": score,
                    "max_score": criterion["max_score"],
                    "reasoning": "AI 분석 결과입니다.",
                    "improvement": "추가 검토를 권장합니다."
                })
        
        return {
            "criteria_scores": criteria_scores,
            "total_score": sum(score["suggested_score"] for score in criteria_scores),
            "overall_comment": text[:500] + "..." if len(text) > 500 else text
        }

# 향상된 AI 서비스 인스턴스
enhanced_ai_service = EnhancedAIService()