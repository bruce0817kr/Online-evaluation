// 초기 데이터베이스 설정 및 샘플 데이터 생성 스크립트
// 중소기업 지원사업 평가 시스템 초기화용

// 데이터베이스 연결
db = db.getSiblingDB('online_evaluation');

// 컬렉션 초기화 (기존 데이터 삭제)
print("기존 데이터 정리 중...");
db.users.deleteMany({});
db.projects.deleteMany({});
db.companies.deleteMany({});
db.templates.deleteMany({});
db.evaluations.deleteMany({});
db.file_metadata.deleteMany({});

// 관리자 계정 생성 (bcrypt 해시 사용)
print("관리자 계정 생성 중...");
const adminUser = {
  "_id": "admin_001",
  "login_id": "admin",
  "password_hash": "$2b$12$LQv3c1yqBwEHxPiuzNW9qe.7nL4JpK4fVqP4VrKL7lWGhk5eG.VPi", // 비밀번호: admin123
  "user_name": "시스템 관리자",
  "email": "admin@evaluation.kr",
  "phone": "02-1234-5678",
  "role": "admin",
  "is_active": true,
  "created_at": new Date(),
  "last_login": null
};

db.users.insertOne(adminUser);

// 간사 계정 생성
print("간사 계정 생성 중...");
const secretaryUser = {
  "_id": "secretary_001",
  "login_id": "secretary01",
  "password_hash": "$2b$12$8k5Y9p3QX2Nf7sR4vW1tMO.BqJhL6uE3nC9gA2sD8fP5xZ7rQ1wE9", // 비밀번호: sec123
  "user_name": "김간사",
  "email": "secretary@evaluation.kr",
  "phone": "02-1234-5679",
  "role": "secretary",
  "is_active": true,
  "created_at": new Date(),
  "last_login": null
};

db.users.insertOne(secretaryUser);

// 평가위원 계정들 생성
print("평가위원 계정 생성 중...");
const evaluators = [
  {
    "_id": "evaluator_001",
    "login_id": "eval001",
    "password_hash": "$2b$12$9m6N0q4RY3Of8tS5wX2uNP.CrKiM7vF4oD0hB3tE9gQ6yA8sR2xF0", // 비밀번호: eval123
    "user_name": "박평가",
    "email": "evaluator01@evaluation.kr",
    "phone": "010-1234-5678",
    "role": "evaluator",
    "is_active": true,
    "created_at": new Date(),
    "last_login": null
  },
  {
    "_id": "evaluator_002", 
    "login_id": "eval002",
    "password_hash": "$2b$12$9m6N0q4RY3Of8tS5wX2uNP.CrKiM7vF4oD0hB3tE9gQ6yA8sR2xF0", // 비밀번호: eval123
    "user_name": "이심사",
    "email": "evaluator02@evaluation.kr", 
    "phone": "010-1234-5679",
    "role": "evaluator",
    "is_active": true,
    "created_at": new Date(),
    "last_login": null
  },
  {
    "_id": "evaluator_003",
    "login_id": "eval003", 
    "password_hash": "$2b$12$9m6N0q4RY3Of8tS5wX2uNP.CrKiM7vF4oD0hB3tE9gQ6yA8sR2xF0", // 비밀번호: eval123
    "user_name": "최검토",
    "email": "evaluator03@evaluation.kr",
    "phone": "010-1234-5680",
    "role": "evaluator", 
    "is_active": true,
    "created_at": new Date(),
    "last_login": null
  }
];

db.users.insertMany(evaluators);

// 샘플 프로젝트 생성 (중소기업 지원사업)
print("샘플 프로젝트 생성 중...");
const projects = [
  {
    "_id": "project_001",
    "name": "2025년 중소기업 디지털 전환 지원사업",
    "description": "중소기업의 디지털 전환을 통한 경쟁력 강화 지원 사업입니다. AI, IoT, 빅데이터 등 4차 산업혁명 기술 도입을 지원합니다.",
    "start_date": new Date("2025-01-01"),
    "end_date": new Date("2025-12-31"),
    "deadline": new Date("2025-03-31"),
    "created_at": new Date(),
    "updated_at": new Date(),
    "created_by": "admin_001",
    "is_active": true
  },
  {
    "_id": "project_002", 
    "name": "2025년 스마트팩토리 구축 지원사업",
    "description": "제조업 중소기업의 스마트팩토리 구축을 통한 생산성 향상 및 품질 개선을 지원하는 사업입니다.",
    "start_date": new Date("2025-02-01"),
    "end_date": new Date("2025-11-30"),
    "deadline": new Date("2025-04-30"),
    "created_at": new Date(),
    "updated_at": new Date(),
    "created_by": "admin_001",
    "is_active": true
  }
];

db.projects.insertMany(projects);

// 샘플 기업 생성
print("샘플 기업 생성 중...");
const companies = [
  {
    "_id": "company_001",
    "name": "테크혁신㈜",
    "registration_number": "123-45-67890",
    "address": "서울시 강남구 테헤란로 123",
    "project_id": "project_001",
    "created_at": new Date()
  },
  {
    "_id": "company_002",
    "name": "스마트제조㈜", 
    "registration_number": "234-56-78901",
    "address": "경기도 성남시 분당구 정자로 456",
    "project_id": "project_001",
    "created_at": new Date()
  },
  {
    "_id": "company_003",
    "name": "미래공장㈜",
    "registration_number": "345-67-89012", 
    "address": "인천시 연수구 송도대로 789",
    "project_id": "project_002",
    "created_at": new Date()
  },
  {
    "_id": "company_004",
    "name": "디지털솔루션㈜",
    "registration_number": "456-78-90123",
    "address": "대전시 유성구 대학로 101",
    "project_id": "project_002", 
    "created_at": new Date()
  }
];

db.companies.insertMany(companies);

// 평가 템플릿 생성 
print("평가 템플릿 생성 중...");
const templates = [
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
    "created_at": new Date(),
    "updated_at": new Date(),
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
    "created_at": new Date(), 
    "updated_at": new Date(),
    "created_by": "admin_001",
    "status": "active"
  }
];

db.templates.insertMany(templates);

// 인덱스 생성 (성능 최적화)
print("인덱스 생성 중...");
db.users.createIndex({ "login_id": 1 }, { unique: true });
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "role": 1 });
db.users.createIndex({ "is_active": 1 });

db.projects.createIndex({ "name": 1 });
db.projects.createIndex({ "is_active": 1 });
db.projects.createIndex({ "created_at": -1 });

db.companies.createIndex({ "name": 1 });
db.companies.createIndex({ "project_id": 1 });
db.companies.createIndex({ "registration_number": 1 }, { unique: true });

db.templates.createIndex({ "project_id": 1 });
db.templates.createIndex({ "status": 1 });
db.templates.createIndex({ "created_at": -1 });

db.evaluations.createIndex({ "evaluator_id": 1 });
db.evaluations.createIndex({ "company_id": 1 });
db.evaluations.createIndex({ "template_id": 1 });
db.evaluations.createIndex({ "status": 1 });
db.evaluations.createIndex({ "submitted_at": -1 });

db.file_metadata.createIndex({ "company_id": 1 });
db.file_metadata.createIndex({ "uploaded_by": 1 });
db.file_metadata.createIndex({ "uploaded_at": -1 });

print("=== 초기 데이터 생성 완료 ===");
print("");
print("✅ 생성된 계정 정보:");
print("📋 관리자 계정:");
print("   - 아이디: admin");
print("   - 비밀번호: admin123");
print("   - 역할: 시스템 관리자");
print("");
print("👥 간사 계정:");
print("   - 아이디: secretary01");
print("   - 비밀번호: sec123");
print("   - 역할: 사업 간사");
print("");
print("⚖️ 평가위원 계정:");
print("   - 아이디: eval001 / 비밀번호: eval123 (박평가)");
print("   - 아이디: eval002 / 비밀번호: eval123 (이심사)");
print("   - 아이디: eval003 / 비밀번호: eval123 (최검토)");
print("");
print("🏢 생성된 프로젝트:");
print("   - 2025년 중소기업 디지털 전환 지원사업");
print("   - 2025년 스마트팩토리 구축 지원사업");
print("");
print("🏭 등록된 기업:");
print("   - 테크혁신㈜, 스마트제조㈜ (디지털 전환 사업)");
print("   - 미래공장㈜, 디지털솔루션㈜ (스마트팩토리 사업)");
print("");
print("📝 평가 템플릿:");
print("   - 디지털 전환 사업 평가 템플릿 (4개 평가 항목)");
print("   - 스마트팩토리 구축 평가 템플릿 (4개 평가 항목)");
print("");
print("🎯 시스템 준비 완료! 웹 브라우저에서 http://localhost:3001로 접속하세요.");