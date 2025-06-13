// MongoDB 초기화 스크립트 - 온라인 평가 시스템
// 컬렉션 생성, 인덱스 설정, 제약조건 적용

// 온라인 평가 데이터베이스 선택
db = db.getSiblingDB('online_evaluation');

print("온라인 평가 시스템 MongoDB 초기화 시작...");

// 1. 컬렉션 생성
print("1. 컬렉션 생성 중...");

const collections = [
    'users',
    'projects', 
    'companies',
    'evaluation_templates',
    'evaluation_sheets',
    'evaluation_scores',
    'secretary_approvals',
    'file_metadata'
];

collections.forEach(collectionName => {
    try {
        db.createCollection(collectionName);
        print(`  ✓ ${collectionName} 컬렉션 생성 완료`);
    } catch (error) {
        if (error.code === 48) {
            print(`  - ${collectionName} 컬렉션이 이미 존재합니다`);
        } else {
            print(`  ✗ ${collectionName} 컬렉션 생성 실패: ${error.message}`);
        }
    }
});

// 2. users 컬렉션 인덱스 설정
print("2. users 컬렉션 인덱스 설정 중...");
try {
    db.users.createIndex({ "login_id": 1 }, { unique: true });
    db.users.createIndex({ "email": 1 }, { unique: true });
    db.users.createIndex({ "role": 1 });
    db.users.createIndex({ "is_active": 1 });
    db.users.createIndex({ "created_at": -1 });
    print("  ✓ users 인덱스 생성 완료");
} catch (error) {
    print(`  ✗ users 인덱스 생성 실패: ${error.message}`);
}

// 3. projects 컬렉션 인덱스 설정
print("3. projects 컬렉션 인덱스 설정 중...");
try {
    db.projects.createIndex({ "id": 1 }, { unique: true });
    db.projects.createIndex({ "created_by": 1 });
    db.projects.createIndex({ "is_active": 1 });
    db.projects.createIndex({ "deadline": 1 });
    db.projects.createIndex({ "created_at": -1 });
    print("  ✓ projects 인덱스 생성 완료");
} catch (error) {
    print(`  ✗ projects 인덱스 생성 실패: ${error.message}`);
}// 4. companies 컬렉션 인덱스 설정  
print("4. companies 컬렉션 인덱스 설정 중...");
try {
    db.companies.createIndex({ "id": 1 }, { unique: true });
    db.companies.createIndex({ "project_id": 1 });
    db.companies.createIndex({ "business_number": 1 });
    db.companies.createIndex({ "evaluation_status": 1 });
    db.companies.createIndex({ "created_at": -1 });
    print("  ✓ companies 인덱스 생성 완료");
} catch (error) {
    print(`  ✗ companies 인덱스 생성 실패: ${error.message}`);
}

// 5. evaluation_templates 컬렉션 인덱스 설정
print("5. evaluation_templates 컬렉션 인덱스 설정 중...");
try {
    db.evaluation_templates.createIndex({ "id": 1 }, { unique: true });
    db.evaluation_templates.createIndex({ "project_id": 1 });
    db.evaluation_templates.createIndex({ "created_by": 1 });
    db.evaluation_templates.createIndex({ "status": 1 });
    db.evaluation_templates.createIndex({ "is_active": 1 });
    db.evaluation_templates.createIndex({ "created_at": -1 });
    print("  ✓ evaluation_templates 인덱스 생성 완료");
} catch (error) {
    print(`  ✗ evaluation_templates 인덱스 생성 실패: ${error.message}`);
}

// 6. evaluation_sheets 컬렉션 인덱스 설정
print("6. evaluation_sheets 컬렉션 인덱스 설정 중...");
try {
    db.evaluation_sheets.createIndex({ "id": 1 }, { unique: true });
    db.evaluation_sheets.createIndex({ "evaluator_id": 1 });
    db.evaluation_sheets.createIndex({ "company_id": 1 });
    db.evaluation_sheets.createIndex({ "project_id": 1 });
    db.evaluation_sheets.createIndex({ "template_id": 1 });
    db.evaluation_sheets.createIndex({ "status": 1 });
    db.evaluation_sheets.createIndex({ "evaluator_id": 1, "status": 1 });
    db.evaluation_sheets.createIndex({ "created_at": -1 });
    print("  ✓ evaluation_sheets 인덱스 생성 완료");
} catch (error) {
    print(`  ✗ evaluation_sheets 인덱스 생성 실패: ${error.message}`);
}

// 7. evaluation_scores 컬렉션 인덱스 설정
print("7. evaluation_scores 컬렉션 인덱스 설정 중...");
try {
    db.evaluation_scores.createIndex({ "id": 1 }, { unique: true });
    db.evaluation_scores.createIndex({ "sheet_id": 1 });
    db.evaluation_scores.createIndex({ "item_id": 1 });
    db.evaluation_scores.createIndex({ "sheet_id": 1, "item_id": 1 });
    db.evaluation_scores.createIndex({ "created_at": -1 });
    print("  ✓ evaluation_scores 인덱스 생성 완료");
} catch (error) {
    print(`  ✗ evaluation_scores 인덱스 생성 실패: ${error.message}`);
}// 8. secretary_approvals 컬렉션 인덱스 설정
print("8. secretary_approvals 컬렉션 인덱스 설정 중...");
try {
    db.secretary_approvals.createIndex({ "id": 1 }, { unique: true });
    db.secretary_approvals.createIndex({ "email": 1 }, { unique: true });
    db.secretary_approvals.createIndex({ "status": 1 });
    db.secretary_approvals.createIndex({ "created_at": -1 });
    print("  ✓ secretary_approvals 인덱스 생성 완료");
} catch (error) {
    print(`  ✗ secretary_approvals 인덱스 생성 실패: ${error.message}`);
}

// 9. file_metadata 컬렉션 인덱스 설정
print("9. file_metadata 컬렉션 인덱스 설정 중...");
try {
    db.file_metadata.createIndex({ "id": 1 }, { unique: true });
    db.file_metadata.createIndex({ "company_id": 1 });
    db.file_metadata.createIndex({ "uploaded_by": 1 });
    db.file_metadata.createIndex({ "file_type": 1 });
    db.file_metadata.createIndex({ "is_processed": 1 });
    db.file_metadata.createIndex({ "uploaded_at": -1 });
    print("  ✓ file_metadata 인덱스 생성 완료");
} catch (error) {
    print(`  ✗ file_metadata 인덱스 생성 실패: ${error.message}`);
}

// 10. 텍스트 검색을 위한 인덱스 생성
print("10. 텍스트 검색 인덱스 설정 중...");
try {
    // 프로젝트 검색용
    db.projects.createIndex({ 
        "name": "text", 
        "description": "text" 
    }, { 
        name: "project_text_search" 
    });
    
    // 회사 검색용
    db.companies.createIndex({ 
        "name": "text", 
        "business_number": "text" 
    }, { 
        name: "company_text_search" 
    });
    
    // 사용자 검색용
    db.users.createIndex({ 
        "user_name": "text", 
        "email": "text", 
        "login_id": "text" 
    }, { 
        name: "user_text_search" 
    });
    
    print("  ✓ 텍스트 검색 인덱스 생성 완료");
} catch (error) {
    print(`  ✗ 텍스트 검색 인덱스 생성 실패: ${error.message}`);
}

// 11. 컬렉션 상태 확인
print("11. 컬렉션 상태 확인 중...");
let totalIndexes = 0;

collections.forEach(collectionName => {
    const indexCount = db[collectionName].getIndexes().length;
    totalIndexes += indexCount;
    print(`  - ${collectionName}: ${indexCount}개 인덱스`);
});

print("\n================================");
print("MongoDB 초기화 완료!");
print("================================");
print(`✓ 데이터베이스: online_evaluation`);
print(`✓ 컬렉션 수: ${collections.length}개`);
print(`✓ 총 인덱스 수: ${totalIndexes}개`);
print("✓ 온라인 평가 시스템 준비 완료");
print("================================");