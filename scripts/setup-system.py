#!/usr/bin/env python3
"""
중소기업 지원사업 평가 시스템 초기 설정 스크립트
Python 환경에서 초기 관리자 계정과 샘플 데이터를 생성합니다.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import json

# 패스워드 컨텍스트 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# MongoDB 연결 설정
MONGO_URL = os.getenv("MONGO_URL", "mongodb://admin:password123@localhost:27017/online_evaluation?authSource=admin")
DB_NAME = "online_evaluation"

async def create_initial_data():
    """초기 데이터 생성"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🔄 기존 데이터 정리 중...")
    # 기존 데이터 삭제
    await db.users.delete_many({})
    await db.projects.delete_many({})
    await db.companies.delete_many({})
    await db.templates.delete_many({})
    await db.evaluations.delete_many({})
    await db.file_metadata.delete_many({})
    
    print("👤 관리자 계정 생성 중...")
    # 관리자 계정 생성
    admin_user = {
        "_id": "admin_001",
        "login_id": "admin",
        "password_hash": pwd_context.hash("admin123"),
        "user_name": "시스템 관리자",
        "email": "admin@evaluation.kr",
        "phone": "02-1234-5678",
        "role": "admin",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "last_login": None
    }
    await db.users.insert_one(admin_user)
    
    print("📋 간사 계정 생성 중...")
    # 간사 계정 생성
    secretary_user = {
        "_id": "secretary_001",
        "login_id": "secretary01",
        "password_hash": pwd_context.hash("sec123"),
        "user_name": "김간사",
        "email": "secretary@evaluation.kr",
        "phone": "02-1234-5679",
        "role": "secretary",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "last_login": None
    }
    await db.users.insert_one(secretary_user)
    
    print("⚖️ 평가위원 계정들 생성 중...")
    # 평가위원 계정들 생성
    evaluators = [
        {
            "_id": "evaluator_001",
            "login_id": "eval001",
            "password_hash": pwd_context.hash("eval123"),
            "user_name": "박평가",
            "email": "evaluator01@evaluation.kr",
            "phone": "010-1234-5678",
            "role": "evaluator",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None
        },
        {
            "_id": "evaluator_002",
            "login_id": "eval002", 
            "password_hash": pwd_context.hash("eval123"),
            "user_name": "이심사",
            "email": "evaluator02@evaluation.kr",
            "phone": "010-1234-5679",
            "role": "evaluator",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None
        },
        {
            "_id": "evaluator_003",
            "login_id": "eval003",
            "password_hash": pwd_context.hash("eval123"),
            "user_name": "최검토",
            "email": "evaluator03@evaluation.kr",
            "phone": "010-1234-5680",
            "role": "evaluator",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None
        }
    ]
    await db.users.insert_many(evaluators)
    
    print("🏢 샘플 프로젝트 생성 중...")
    # 샘플 프로젝트 생성
    projects = [
        {
            "_id": "project_001",
            "name": "2025년 중소기업 디지털 전환 지원사업",
            "description": "중소기업의 디지털 전환을 통한 경쟁력 강화 지원 사업입니다. AI, IoT, 빅데이터 등 4차 산업혁명 기술 도입을 지원합니다.",
            "start_date": datetime(2025, 1, 1),
            "end_date": datetime(2025, 12, 31),
            "deadline": datetime(2025, 3, 31),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "admin_001",
            "is_active": True
        },
        {
            "_id": "project_002",
            "name": "2025년 스마트팩토리 구축 지원사업",
            "description": "제조업 중소기업의 스마트팩토리 구축을 통한 생산성 향상 및 품질 개선을 지원하는 사업입니다.",
            "start_date": datetime(2025, 2, 1),
            "end_date": datetime(2025, 11, 30),
            "deadline": datetime(2025, 4, 30),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "admin_001",
            "is_active": True
        }
    ]
    await db.projects.insert_many(projects)
    
    print("🏭 샘플 기업 생성 중...")
    # 샘플 기업 생성
    companies = [
        {
            "_id": "company_001",
            "name": "테크혁신㈜",
            "registration_number": "123-45-67890",
            "address": "서울시 강남구 테헤란로 123",
            "project_id": "project_001",
            "created_at": datetime.utcnow()
        },
        {
            "_id": "company_002",
            "name": "스마트제조㈜",
            "registration_number": "234-56-78901",
            "address": "경기도 성남시 분당구 정자로 456",
            "project_id": "project_001",
            "created_at": datetime.utcnow()
        },
        {
            "_id": "company_003", 
            "name": "미래공장㈜",
            "registration_number": "345-67-89012",
            "address": "인천시 연수구 송도대로 789",
            "project_id": "project_002",
            "created_at": datetime.utcnow()
        },
        {
            "_id": "company_004",
            "name": "디지털솔루션㈜",
            "registration_number": "456-78-90123",
            "address": "대전시 유성구 대학로 101",
            "project_id": "project_002",
            "created_at": datetime.utcnow()
        }
    ]
    await db.companies.insert_many(companies)
    
    print("📝 평가 템플릿 생성 중...")
    # 평가 템플릿 생성
    templates = [
        {
            "_id": "template_001",
            "name": "디지털 전환 사업 평가 템플릿",
            "description": "중소기업 디지털 전환 지원사업 평가를 위한 표준 템플릿입니다.",
            "project_id": "project_001",
            "items": [
                {
                    "id": "item_001",
                    "title": "사업 계획의 적정성",
                    "description": "제출된 사업계획서의 구체성, 실현가능성, 창의성을 평가합니다.",
                    "max_score": 20,
                    "weight": 0.25
                },
                {
                    "id": "item_002",
                    "title": "기술 혁신성",
                    "description": "도입하고자 하는 기술의 혁신성과 차별성을 평가합니다.",
                    "max_score": 25,
                    "weight": 0.3
                },
                {
                    "id": "item_003",
                    "title": "사업화 가능성",
                    "description": "시장성, 경쟁력, 수익성 등 사업화 가능성을 평가합니다.",
                    "max_score": 20,
                    "weight": 0.25
                },
                {
                    "id": "item_004",
                    "title": "추진 역량",
                    "description": "기업의 기술적, 재정적, 인적 추진 역량을 평가합니다.",
                    "max_score": 15,
                    "weight": 0.2
                }
            ],
            "total_score": 100,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "admin_001",
            "status": "active"
        },
        {
            "_id": "template_002",
            "name": "스마트팩토리 구축 평가 템플릿",
            "description": "스마트팩토리 구축 지원사업 평가를 위한 전문 템플릿입니다.",
            "project_id": "project_002",
            "items": [
                {
                    "id": "item_101",
                    "title": "현황 분석의 적정성",
                    "description": "현재 제조 시설 및 공정 분석의 정확성과 개선 필요성 파악도를 평가합니다.",
                    "max_score": 15,
                    "weight": 0.2
                },
                {
                    "id": "item_102",
                    "title": "스마트팩토리 설계",
                    "description": "IoT, AI, 자동화 등 스마트팩토리 기술 적용 계획의 적정성을 평가합니다.",
                    "max_score": 30,
                    "weight": 0.35
                },
                {
                    "id": "item_103",
                    "title": "투자 효과성",
                    "description": "투자 대비 생산성 향상, 품질 개선 등 기대 효과의 합리성을 평가합니다.",
                    "max_score": 25,
                    "weight": 0.3
                },
                {
                    "id": "item_104",
                    "title": "구축 및 운영 계획",
                    "description": "단계별 구축 계획과 완료 후 운영 방안의 실현가능성을 평가합니다.",
                    "max_score": 15,
                    "weight": 0.15
                }
            ],
            "total_score": 100,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "admin_001",
            "status": "active"
        }
    ]
    await db.templates.insert_many(templates)
    
    print("📊 인덱스 생성 중...")
    # 인덱스 생성
    await db.users.create_index("login_id", unique=True)
    await db.users.create_index("email", unique=True)
    await db.users.create_index("role")
    await db.users.create_index("is_active")
    
    await db.projects.create_index("name")
    await db.projects.create_index("is_active")
    await db.projects.create_index([("created_at", -1)])
    
    await db.companies.create_index("name")
    await db.companies.create_index("project_id")
    await db.companies.create_index("registration_number", unique=True)
    
    await db.templates.create_index("project_id")
    await db.templates.create_index("status")
    await db.templates.create_index([("created_at", -1)])
    
    await db.evaluations.create_index("evaluator_id")
    await db.evaluations.create_index("company_id")
    await db.evaluations.create_index("template_id")
    await db.evaluations.create_index("status")
    await db.evaluations.create_index([("submitted_at", -1)])
    
    await db.file_metadata.create_index("company_id")
    await db.file_metadata.create_index("uploaded_by")
    await db.file_metadata.create_index([("uploaded_at", -1)])
    
    client.close()
    
    print("\n" + "="*50)
    print("🎉 초기 데이터 생성 완료!")
    print("="*50)
    print()
    print("✅ 생성된 계정 정보:")
    print("📋 관리자 계정:")
    print("   - 아이디: admin")
    print("   - 비밀번호: admin123")
    print("   - 역할: 시스템 관리자")
    print()
    print("👥 간사 계정:")
    print("   - 아이디: secretary01") 
    print("   - 비밀번호: sec123")
    print("   - 역할: 사업 간사")
    print()
    print("⚖️ 평가위원 계정:")
    print("   - 아이디: eval001 / 비밀번호: eval123 (박평가)")
    print("   - 아이디: eval002 / 비밀번호: eval123 (이심사)")
    print("   - 아이디: eval003 / 비밀번호: eval123 (최검토)")
    print()
    print("🏢 생성된 프로젝트:")
    print("   - 2025년 중소기업 디지털 전환 지원사업")
    print("   - 2025년 스마트팩토리 구축 지원사업")
    print()
    print("🏭 등록된 기업:")
    print("   - 테크혁신㈜, 스마트제조㈜ (디지털 전환 사업)")
    print("   - 미래공장㈜, 디지털솔루션㈜ (스마트팩토리 사업)")
    print()
    print("📝 평가 템플릿:")
    print("   - 디지털 전환 사업 평가 템플릿 (4개 평가 항목)")
    print("   - 스마트팩토리 구축 평가 템플릿 (4개 평가 항목)")
    print()
    print("🎯 시스템 준비 완료! 웹 브라우저에서 http://localhost:3001로 접속하세요.")

if __name__ == "__main__":
    try:
        asyncio.run(create_initial_data())
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        sys.exit(1)