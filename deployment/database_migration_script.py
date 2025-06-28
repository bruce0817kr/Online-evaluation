#!/usr/bin/env python3
"""
🗄️ AI 모델 관리 시스템 - 데이터베이스 마이그레이션 스크립트
스테이징 환경 DocumentDB 클러스터 초기화 및 최적화

기능:
- MongoDB 스키마 및 인덱스 생성
- 성능 최적화된 인덱스 구성
- 초기 데이터 시딩
- 데이터 무결성 검증
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import motor.motor_asyncio
from pymongo import ASCENDING, DESCENDING, TEXT, GEO2D
from pymongo.errors import DuplicateKeyError, OperationFailure
import bcrypt

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class IndexDefinition:
    """인덱스 정의"""
    collection: str
    fields: List[tuple]
    name: str
    unique: bool = False
    sparse: bool = False
    background: bool = True

@dataclass
class MigrationResult:
    """마이그레이션 결과"""
    collection: str
    operation: str
    status: str
    duration_ms: float
    details: str

class DatabaseMigrator:
    """데이터베이스 마이그레이션 관리자"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.client = None
        self.db = None
        self.migration_results: List[MigrationResult] = []
        
    async def connect(self):
        """데이터베이스 연결"""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(self.connection_string)
            self.db = self.client.online_evaluation
            
            # 연결 테스트
            await self.client.admin.command('ping')
            logger.info("✅ DocumentDB 연결 성공")
            
        except Exception as e:
            logger.error(f"❌ 데이터베이스 연결 실패: {e}")
            raise
    
    async def disconnect(self):
        """데이터베이스 연결 해제"""
        if self.client:
            self.client.close()
            logger.info("🔌 데이터베이스 연결 해제")
    
    def _define_optimized_indexes(self) -> List[IndexDefinition]:
        """성능 최적화된 인덱스 정의"""
        return [
            # 사용자 컬렉션 인덱스
            IndexDefinition(
                collection="users",
                fields=[("login_id", ASCENDING)],
                name="idx_users_login_id",
                unique=True
            ),
            IndexDefinition(
                collection="users",
                fields=[("email", ASCENDING)],
                name="idx_users_email",
                unique=True
            ),
            IndexDefinition(
                collection="users",
                fields=[("role", ASCENDING), ("company_id", ASCENDING)],
                name="idx_users_role_company"
            ),
            IndexDefinition(
                collection="users",
                fields=[("created_at", DESCENDING)],
                name="idx_users_created_at"
            ),
            
            # 회사 컬렉션 인덱스
            IndexDefinition(
                collection="companies",
                fields=[("name", ASCENDING)],
                name="idx_companies_name",
                unique=True
            ),
            IndexDefinition(
                collection="companies",
                fields=[("created_at", DESCENDING)],
                name="idx_companies_created_at"
            ),
            
            # 프로젝트 컬렉션 인덱스
            IndexDefinition(
                collection="projects",
                fields=[("company_id", ASCENDING), ("name", ASCENDING)],
                name="idx_projects_company_name"
            ),
            IndexDefinition(
                collection="projects",
                fields=[("status", ASCENDING), ("created_at", DESCENDING)],
                name="idx_projects_status_created"
            ),
            IndexDefinition(
                collection="projects",
                fields=[("manager_id", ASCENDING)],
                name="idx_projects_manager"
            ),
            
            # 템플릿 컬렉션 인덱스
            IndexDefinition(
                collection="templates",
                fields=[("company_id", ASCENDING), ("name", ASCENDING)],
                name="idx_templates_company_name"
            ),
            IndexDefinition(
                collection="templates",
                fields=[("category", ASCENDING), ("is_active", ASCENDING)],
                name="idx_templates_category_active"
            ),
            IndexDefinition(
                collection="templates",
                fields=[("created_by", ASCENDING), ("created_at", DESCENDING)],
                name="idx_templates_created_by_date"
            ),
            
            # 평가 컬렉션 인덱스
            IndexDefinition(
                collection="evaluations",
                fields=[("project_id", ASCENDING), ("evaluator_id", ASCENDING)],
                name="idx_evaluations_project_evaluator"
            ),
            IndexDefinition(
                collection="evaluations",
                fields=[("status", ASCENDING), ("submitted_at", DESCENDING)],
                name="idx_evaluations_status_submitted"
            ),
            IndexDefinition(
                collection="evaluations",
                fields=[("company_id", ASCENDING), ("created_at", DESCENDING)],
                name="idx_evaluations_company_created"
            ),
            IndexDefinition(
                collection="evaluations",
                fields=[("total_score", DESCENDING)],
                name="idx_evaluations_total_score"
            ),
            
            # 파일 컬렉션 인덱스
            IndexDefinition(
                collection="files",
                fields=[("company_id", ASCENDING), ("file_type", ASCENDING)],
                name="idx_files_company_type"
            ),
            IndexDefinition(
                collection="files",
                fields=[("uploaded_by", ASCENDING), ("uploaded_at", DESCENDING)],
                name="idx_files_uploaded_by_date"
            ),
            IndexDefinition(
                collection="files",
                fields=[("file_hash", ASCENDING)],
                name="idx_files_hash",
                unique=True
            ),
            
            # 텍스트 검색 인덱스
            IndexDefinition(
                collection="templates",
                fields=[("name", TEXT), ("description", TEXT)],
                name="idx_templates_text_search"
            ),
            IndexDefinition(
                collection="projects",
                fields=[("name", TEXT), ("description", TEXT)],
                name="idx_projects_text_search"
            )
        ]
    
    async def create_collections_and_indexes(self) -> Dict[str, Any]:
        """컬렉션 및 인덱스 생성"""
        logger.info("🗂️ 컬렉션 및 인덱스 생성 시작")
        
        collections = ["users", "companies", "projects", "templates", "evaluations", "files"]
        index_definitions = self._define_optimized_indexes()
        
        results = {
            "collections_created": [],
            "indexes_created": [],
            "errors": []
        }
        
        # 컬렉션 생성
        for collection_name in collections:
            try:
                start_time = datetime.now()
                
                # 컬렉션이 존재하지 않으면 생성
                if collection_name not in await self.db.list_collection_names():
                    await self.db.create_collection(collection_name)
                    duration = (datetime.now() - start_time).total_seconds() * 1000
                    
                    result = MigrationResult(
                        collection=collection_name,
                        operation="create_collection",
                        status="success",
                        duration_ms=duration,
                        details=f"컬렉션 {collection_name} 생성 완료"
                    )
                    self.migration_results.append(result)
                    results["collections_created"].append(collection_name)
                    logger.info(f"✅ 컬렉션 생성: {collection_name}")
                else:
                    logger.info(f"⚠️ 컬렉션 이미 존재: {collection_name}")
                    
            except Exception as e:
                error_msg = f"컬렉션 {collection_name} 생성 실패: {e}"
                results["errors"].append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        # 인덱스 생성
        for index_def in index_definitions:
            try:
                start_time = datetime.now()
                collection = self.db[index_def.collection]
                
                # 인덱스 생성 옵션
                index_options = {
                    "name": index_def.name,
                    "unique": index_def.unique,
                    "sparse": index_def.sparse,
                    "background": index_def.background
                }
                
                # 인덱스 생성
                await collection.create_index(
                    index_def.fields,
                    **index_options
                )
                
                duration = (datetime.now() - start_time).total_seconds() * 1000
                
                result = MigrationResult(
                    collection=index_def.collection,
                    operation="create_index",
                    status="success",
                    duration_ms=duration,
                    details=f"인덱스 {index_def.name} 생성 완료"
                )
                self.migration_results.append(result)
                results["indexes_created"].append(index_def.name)
                logger.info(f"✅ 인덱스 생성: {index_def.name} on {index_def.collection}")
                
            except DuplicateKeyError:
                logger.info(f"⚠️ 인덱스 이미 존재: {index_def.name}")
            except Exception as e:
                error_msg = f"인덱스 {index_def.name} 생성 실패: {e}"
                results["errors"].append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        logger.info("✅ 컬렉션 및 인덱스 생성 완료")
        return results
    
    async def seed_initial_data(self) -> Dict[str, Any]:
        """초기 데이터 시딩"""
        logger.info("🌱 초기 데이터 시딩 시작")
        
        results = {
            "data_seeded": [],
            "errors": []
        }
        
        try:
            # 1. 시스템 관리자 생성
            admin_data = await self._create_system_admin()
            if admin_data:
                results["data_seeded"].append("system_admin")
                logger.info("✅ 시스템 관리자 생성 완료")
            
            # 2. 기본 회사 생성
            company_data = await self._create_default_companies()
            if company_data:
                results["data_seeded"].extend(company_data)
                logger.info("✅ 기본 회사 데이터 생성 완료")
            
            # 3. 샘플 템플릿 생성
            template_data = await self._create_sample_templates()
            if template_data:
                results["data_seeded"].extend(template_data)
                logger.info("✅ 샘플 템플릿 생성 완료")
            
            # 4. 테스트 사용자 생성
            user_data = await self._create_test_users()
            if user_data:
                results["data_seeded"].extend(user_data)
                logger.info("✅ 테스트 사용자 생성 완료")
                
        except Exception as e:
            error_msg = f"초기 데이터 시딩 실패: {e}"
            results["errors"].append(error_msg)
            logger.error(f"❌ {error_msg}")
        
        logger.info("✅ 초기 데이터 시딩 완료")
        return results
    
    async def _create_system_admin(self) -> Optional[str]:
        """시스템 관리자 생성"""
        try:
            # 관리자가 이미 존재하는지 확인
            existing_admin = await self.db.users.find_one({"login_id": "admin"})
            if existing_admin:
                logger.info("⚠️ 시스템 관리자 이미 존재")
                return None
            
            # 비밀번호 해싱
            password_hash = bcrypt.hashpw("admin123!".encode('utf-8'), bcrypt.gensalt())
            
            admin_user = {
                "_id": "admin_001",
                "login_id": "admin",
                "name": "시스템 관리자",
                "email": "admin@system.com",
                "password_hash": password_hash.decode('utf-8'),
                "role": "admin",
                "company_id": "system",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_login": None,
                "login_attempts": 0,
                "profile": {
                    "phone": "010-0000-0000",
                    "department": "시스템",
                    "position": "관리자"
                }
            }
            
            await self.db.users.insert_one(admin_user)
            return "admin_user"
            
        except Exception as e:
            logger.error(f"❌ 시스템 관리자 생성 실패: {e}")
            return None
    
    async def _create_default_companies(self) -> List[str]:
        """기본 회사 생성"""
        try:
            companies = [
                {
                    "_id": "company_001",
                    "name": "시스템 회사",
                    "business_number": "000-00-00000",
                    "address": "서울시 강남구",
                    "contact_email": "contact@system.com",
                    "contact_phone": "02-0000-0000",
                    "is_active": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "settings": {
                        "max_users": 1000,
                        "max_projects": 100,
                        "storage_limit_gb": 10
                    }
                },
                {
                    "_id": "company_002", 
                    "name": "테스트 회사",
                    "business_number": "111-11-11111",
                    "address": "서울시 서초구",
                    "contact_email": "test@company.com",
                    "contact_phone": "02-1111-1111",
                    "is_active": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "settings": {
                        "max_users": 50,
                        "max_projects": 20,
                        "storage_limit_gb": 5
                    }
                }
            ]
            
            created_companies = []
            for company in companies:
                try:
                    # 회사가 이미 존재하는지 확인
                    existing = await self.db.companies.find_one({"name": company["name"]})
                    if not existing:
                        await self.db.companies.insert_one(company)
                        created_companies.append(f"company_{company['name']}")
                        logger.info(f"✅ 회사 생성: {company['name']}")
                    else:
                        logger.info(f"⚠️ 회사 이미 존재: {company['name']}")
                except Exception as e:
                    logger.error(f"❌ 회사 생성 실패 {company['name']}: {e}")
            
            return created_companies
            
        except Exception as e:
            logger.error(f"❌ 기본 회사 생성 실패: {e}")
            return []
    
    async def _create_sample_templates(self) -> List[str]:
        """샘플 템플릿 생성"""
        try:
            templates = [
                {
                    "_id": "template_001",
                    "name": "기본 평가 템플릿",
                    "description": "일반적인 평가를 위한 기본 템플릿",
                    "company_id": "company_001",
                    "category": "general",
                    "criteria": [
                        {
                            "id": "quality",
                            "name": "품질",
                            "description": "작업의 전반적인 품질",
                            "weight": 30,
                            "max_score": 100
                        },
                        {
                            "id": "efficiency",
                            "name": "효율성",
                            "description": "작업의 효율성과 속도",
                            "weight": 25,
                            "max_score": 100
                        },
                        {
                            "id": "creativity",
                            "name": "창의성",
                            "description": "창의적 접근과 혁신성",
                            "weight": 20,
                            "max_score": 100
                        },
                        {
                            "id": "communication",
                            "name": "소통",
                            "description": "의사소통 능력",
                            "weight": 15,
                            "max_score": 100
                        },
                        {
                            "id": "teamwork",
                            "name": "팀워크",
                            "description": "팀 협력 능력",
                            "weight": 10,
                            "max_score": 100
                        }
                    ],
                    "is_active": True,
                    "created_by": "admin_001",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                {
                    "_id": "template_002",
                    "name": "AI 모델 평가 템플릿",
                    "description": "AI 모델 성능 평가를 위한 전문 템플릿",
                    "company_id": "company_001",
                    "category": "ai_model",
                    "criteria": [
                        {
                            "id": "accuracy",
                            "name": "정확도",
                            "description": "모델 예측 정확도",
                            "weight": 40,
                            "max_score": 100
                        },
                        {
                            "id": "performance",
                            "name": "성능",
                            "description": "처리 속도 및 리소스 효율성",
                            "weight": 30,
                            "max_score": 100
                        },
                        {
                            "id": "robustness",
                            "name": "견고성",
                            "description": "다양한 입력에 대한 안정성",
                            "weight": 20,
                            "max_score": 100
                        },
                        {
                            "id": "interpretability",
                            "name": "해석가능성",
                            "description": "모델 결과의 해석 용이성",
                            "weight": 10,
                            "max_score": 100
                        }
                    ],
                    "is_active": True,
                    "created_by": "admin_001",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            ]
            
            created_templates = []
            for template in templates:
                try:
                    # 템플릿이 이미 존재하는지 확인
                    existing = await self.db.templates.find_one({"name": template["name"]})
                    if not existing:
                        await self.db.templates.insert_one(template)
                        created_templates.append(f"template_{template['name']}")
                        logger.info(f"✅ 템플릿 생성: {template['name']}")
                    else:
                        logger.info(f"⚠️ 템플릿 이미 존재: {template['name']}")
                except Exception as e:
                    logger.error(f"❌ 템플릿 생성 실패 {template['name']}: {e}")
            
            return created_templates
            
        except Exception as e:
            logger.error(f"❌ 샘플 템플릿 생성 실패: {e}")
            return []
    
    async def _create_test_users(self) -> List[str]:
        """테스트 사용자 생성"""
        try:
            # 비밀번호 해싱
            password_hash = bcrypt.hashpw("test123!".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            users = [
                {
                    "_id": "user_001",
                    "login_id": "manager1",
                    "name": "김매니저",
                    "email": "manager1@test.com",
                    "password_hash": password_hash,
                    "role": "manager",
                    "company_id": "company_002",
                    "is_active": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "profile": {
                        "phone": "010-1234-5678",
                        "department": "개발팀",
                        "position": "팀장"
                    }
                },
                {
                    "_id": "user_002",
                    "login_id": "evaluator1",
                    "name": "이평가자",
                    "email": "evaluator1@test.com",
                    "password_hash": password_hash,
                    "role": "evaluator",
                    "company_id": "company_002",
                    "is_active": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "profile": {
                        "phone": "010-2345-6789",
                        "department": "QA팀",
                        "position": "수석연구원"
                    }
                },
                {
                    "_id": "user_003",
                    "login_id": "secretary1",
                    "name": "박간사",
                    "email": "secretary1@test.com",
                    "password_hash": password_hash,
                    "role": "secretary",
                    "company_id": "company_002",
                    "is_active": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "profile": {
                        "phone": "010-3456-7890",
                        "department": "경영지원팀",
                        "position": "대리"
                    }
                }
            ]
            
            created_users = []
            for user in users:
                try:
                    # 사용자가 이미 존재하는지 확인
                    existing = await self.db.users.find_one({"login_id": user["login_id"]})
                    if not existing:
                        await self.db.users.insert_one(user)
                        created_users.append(f"user_{user['login_id']}")
                        logger.info(f"✅ 사용자 생성: {user['login_id']}")
                    else:
                        logger.info(f"⚠️ 사용자 이미 존재: {user['login_id']}")
                except Exception as e:
                    logger.error(f"❌ 사용자 생성 실패 {user['login_id']}: {e}")
            
            return created_users
            
        except Exception as e:
            logger.error(f"❌ 테스트 사용자 생성 실패: {e}")
            return []
    
    async def verify_data_integrity(self) -> Dict[str, Any]:
        """데이터 무결성 검증"""
        logger.info("🔍 데이터 무결성 검증 시작")
        
        verification_results = {
            "collection_counts": {},
            "index_verification": {},
            "data_integrity_checks": [],
            "errors": []
        }
        
        try:
            # 1. 컬렉션별 문서 수 확인
            collections = ["users", "companies", "projects", "templates", "evaluations", "files"]
            for collection_name in collections:
                count = await self.db[collection_name].count_documents({})
                verification_results["collection_counts"][collection_name] = count
                logger.info(f"📊 {collection_name}: {count}개 문서")
            
            # 2. 인덱스 존재 확인
            index_definitions = self._define_optimized_indexes()
            for index_def in index_definitions:
                try:
                    collection = self.db[index_def.collection]
                    indexes = await collection.list_indexes().to_list(length=None)
                    index_names = [idx["name"] for idx in indexes]
                    
                    exists = index_def.name in index_names
                    verification_results["index_verification"][index_def.name] = exists
                    
                    if exists:
                        logger.info(f"✅ 인덱스 확인: {index_def.name}")
                    else:
                        logger.warning(f"⚠️ 인덱스 누락: {index_def.name}")
                        
                except Exception as e:
                    error_msg = f"인덱스 확인 실패 {index_def.name}: {e}"
                    verification_results["errors"].append(error_msg)
                    logger.error(f"❌ {error_msg}")
            
            # 3. 데이터 무결성 검사
            integrity_checks = [
                await self._check_user_data_integrity(),
                await self._check_company_data_integrity(),
                await self._check_template_data_integrity()
            ]
            
            verification_results["data_integrity_checks"] = integrity_checks
            
            # 4. 성능 테스트 쿼리
            performance_results = await self._run_performance_queries()
            verification_results["performance_test"] = performance_results
            
        except Exception as e:
            error_msg = f"데이터 무결성 검증 실패: {e}"
            verification_results["errors"].append(error_msg)
            logger.error(f"❌ {error_msg}")
        
        logger.info("✅ 데이터 무결성 검증 완료")
        return verification_results
    
    async def _check_user_data_integrity(self) -> Dict[str, Any]:
        """사용자 데이터 무결성 검사"""
        try:
            # 중복 login_id 검사
            pipeline = [
                {"$group": {"_id": "$login_id", "count": {"$sum": 1}}},
                {"$match": {"count": {"$gt": 1}}}
            ]
            duplicates = await self.db.users.aggregate(pipeline).to_list(length=None)
            
            # 유효하지 않은 이메일 검사
            invalid_emails = await self.db.users.count_documents({
                "email": {"$not": {"$regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"}}
            })
            
            return {
                "check_name": "user_data_integrity",
                "duplicate_login_ids": len(duplicates),
                "invalid_emails": invalid_emails,
                "status": "pass" if len(duplicates) == 0 and invalid_emails == 0 else "warning"
            }
            
        except Exception as e:
            return {
                "check_name": "user_data_integrity",
                "status": "error",
                "error": str(e)
            }
    
    async def _check_company_data_integrity(self) -> Dict[str, Any]:
        """회사 데이터 무결성 검사"""
        try:
            # 중복 회사명 검사
            pipeline = [
                {"$group": {"_id": "$name", "count": {"$sum": 1}}},
                {"$match": {"count": {"$gt": 1}}}
            ]
            duplicates = await self.db.companies.aggregate(pipeline).to_list(length=None)
            
            return {
                "check_name": "company_data_integrity", 
                "duplicate_company_names": len(duplicates),
                "status": "pass" if len(duplicates) == 0 else "warning"
            }
            
        except Exception as e:
            return {
                "check_name": "company_data_integrity",
                "status": "error",
                "error": str(e)
            }
    
    async def _check_template_data_integrity(self) -> Dict[str, Any]:
        """템플릿 데이터 무결성 검사"""
        try:
            # 가중치 합계가 100이 아닌 템플릿 검사
            templates = await self.db.templates.find({}).to_list(length=None)
            invalid_weights = []
            
            for template in templates:
                total_weight = sum(criterion.get("weight", 0) for criterion in template.get("criteria", []))
                if total_weight != 100:
                    invalid_weights.append(template["_id"])
            
            return {
                "check_name": "template_data_integrity",
                "invalid_weight_templates": len(invalid_weights),
                "status": "pass" if len(invalid_weights) == 0 else "warning"
            }
            
        except Exception as e:
            return {
                "check_name": "template_data_integrity",
                "status": "error",
                "error": str(e)
            }
    
    async def _run_performance_queries(self) -> Dict[str, Any]:
        """성능 테스트 쿼리 실행"""
        try:
            performance_results = {}
            
            # 1. 사용자 조회 성능 테스트
            start_time = datetime.now()
            await self.db.users.find_one({"login_id": "admin"})
            user_query_time = (datetime.now() - start_time).total_seconds() * 1000
            performance_results["user_lookup_ms"] = user_query_time
            
            # 2. 회사별 사용자 수 집계 성능 테스트
            start_time = datetime.now()
            pipeline = [
                {"$group": {"_id": "$company_id", "user_count": {"$sum": 1}}}
            ]
            await self.db.users.aggregate(pipeline).to_list(length=None)
            aggregation_time = (datetime.now() - start_time).total_seconds() * 1000
            performance_results["user_aggregation_ms"] = aggregation_time
            
            # 3. 템플릿 텍스트 검색 성능 테스트
            start_time = datetime.now()
            await self.db.templates.find({"$text": {"$search": "평가"}}).to_list(length=10)
            text_search_time = (datetime.now() - start_time).total_seconds() * 1000
            performance_results["text_search_ms"] = text_search_time
            
            return {
                "status": "success",
                "queries": performance_results,
                "average_query_time": sum(performance_results.values()) / len(performance_results)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def generate_migration_report(self) -> Dict[str, Any]:
        """마이그레이션 리포트 생성"""
        logger.info("📋 마이그레이션 리포트 생성")
        
        # 성공/실패 통계
        total_operations = len(self.migration_results)
        successful_operations = len([r for r in self.migration_results if r.status == "success"])
        
        # 평균 실행 시간
        avg_duration = sum(r.duration_ms for r in self.migration_results) / total_operations if total_operations > 0 else 0
        
        # 컬렉션별 통계
        collection_stats = {}
        for result in self.migration_results:
            if result.collection not in collection_stats:
                collection_stats[result.collection] = {"operations": 0, "avg_duration": 0}
            collection_stats[result.collection]["operations"] += 1
        
        report = {
            "migration_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_operations": total_operations,
                "successful_operations": successful_operations,
                "success_rate": (successful_operations / total_operations * 100) if total_operations > 0 else 0,
                "average_duration_ms": avg_duration
            },
            "detailed_results": [
                {
                    "collection": r.collection,
                    "operation": r.operation,
                    "status": r.status,
                    "duration_ms": r.duration_ms,
                    "details": r.details
                }
                for r in self.migration_results
            ],
            "collection_statistics": collection_stats,
            "recommendations": [
                "정기적인 인덱스 성능 모니터링 수행",
                "데이터 증가에 따른 인덱스 최적화 검토",
                "백업 및 복구 프로세스 정기 테스트",
                "성능 저하 시 쿼리 실행 계획 분석"
            ]
        }
        
        return report

async def main():
    """메인 실행 함수"""
    # 환경 변수에서 연결 정보 가져오기
    mongo_url = os.getenv('MONGO_URL', 'mongodb://admin:password123@localhost:27017/online_evaluation')
    
    migrator = DatabaseMigrator(mongo_url)
    
    try:
        print("🗄️ AI 모델 관리 시스템 - 데이터베이스 마이그레이션")
        print("스테이징 환경 DocumentDB 초기화 시작\n")
        
        # 1. 데이터베이스 연결
        await migrator.connect()
        
        # 2. 컬렉션 및 인덱스 생성
        print("🏗️ 컬렉션 및 인덱스 생성 중...")
        schema_results = await migrator.create_collections_and_indexes()
        print(f"✅ 컬렉션 {len(schema_results['collections_created'])}개, 인덱스 {len(schema_results['indexes_created'])}개 생성")
        
        # 3. 초기 데이터 시딩
        print("\n🌱 초기 데이터 시딩 중...")
        seed_results = await migrator.seed_initial_data()
        print(f"✅ 데이터 항목 {len(seed_results['data_seeded'])}개 생성")
        
        # 4. 데이터 무결성 검증
        print("\n🔍 데이터 무결성 검증 중...")
        verification_results = await migrator.verify_data_integrity()
        print(f"✅ 무결성 검사 완료 - 평균 쿼리 시간: {verification_results['performance_test']['average_query_time']:.2f}ms")
        
        # 5. 마이그레이션 리포트 생성
        report = await migrator.generate_migration_report()
        
        # 리포트 저장
        report_file = f"/tmp/database_migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 마이그레이션 리포트 저장: {report_file}")
        
        # 결과 요약 출력
        print("\n" + "="*60)
        print("🎯 데이터베이스 마이그레이션 완료")
        print("="*60)
        print(f"🏗️ 총 작업: {report['migration_summary']['total_operations']}개")
        print(f"✅ 성공률: {report['migration_summary']['success_rate']:.1f}%")
        print(f"⏱️ 평균 실행시간: {report['migration_summary']['average_duration_ms']:.1f}ms")
        
        # 컬렉션별 데이터 수 출력
        print(f"\n📊 생성된 데이터:")
        for collection, count in verification_results["collection_counts"].items():
            print(f"  - {collection}: {count}개")
        
        print("\n🚀 데이터베이스 마이그레이션 성공!")
        
    except Exception as e:
        print(f"\n❌ 마이그레이션 실패: {e}")
        raise
    finally:
        await migrator.disconnect()

if __name__ == "__main__":
    asyncio.run(main())