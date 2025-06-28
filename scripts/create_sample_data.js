/**
 * 온라인 평가 시스템 - 샘플 프로젝트 및 회사 데이터 생성 스크립트
 * 실행: mongosh --file create_sample_data.js
 */

// 데이터베이스 연결 (프로덕션 환경용으로 변경)
use('online_evaluation_prod');

// UUID 생성 함수
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// 날짜 생성 함수
function getRandomDate(daysFromNow, range = 30) {
    const now = new Date();
    const targetDate = new Date(now);
    targetDate.setDate(now.getDate() + daysFromNow);
    
    if (range > 0) {
        const randomDays = Math.floor(Math.random() * range) - (range / 2);
        targetDate.setDate(targetDate.getDate() + randomDays);
    }
    
    return targetDate;
}

// 기존 사용자 조회
const existingUsers = db.users.find({}).toArray();
const adminUser = existingUsers.find(user => user.role === 'admin');
const secretaries = existingUsers.filter(user => user.role === 'secretary');
const evaluators = existingUsers.filter(user => user.role === 'evaluator');

if (!adminUser) {
    print("오류: admin 사용자를 찾을 수 없습니다.");
    quit(1);
}

print(`기존 사용자 발견: admin(1), secretary(${secretaries.length}), evaluator(${evaluators.length})`);// 샘플 프로젝트 데이터
const sampleProjects = [
    {
        id: generateUUID(),
        name: "2024년 차세대 IT기업 평가 프로젝트",
        description: "국내 유망 IT 스타트업 및 중소기업의 기술력, 시장성, 성장 가능성을 종합적으로 평가하여 투자 및 지원 대상을 선정하는 프로젝트입니다.",
        deadline: getRandomDate(45, 10),
        created_by: adminUser.id,
        created_at: new Date(),
        is_active: true,
        total_companies: 0,
        total_evaluations: 0,
        completed_evaluations: 0
    },
    {
        id: generateUUID(),
        name: "바이오헬스케어 기업 역량 평가",
        description: "바이오의약품, 의료기기, 디지털헬스케어 분야의 기업들을 대상으로 R&D 역량, 사업화 가능성, 규제 대응 능력을 평가합니다.",
        deadline: getRandomDate(60, 15),
        created_by: adminUser.id,
        created_at: new Date(),
        is_active: true,
        total_companies: 0,
        total_evaluations: 0,
        completed_evaluations: 0
    },
    {
        id: generateUUID(),
        name: "그린테크 혁신기업 발굴 평가",
        description: "신재생에너지, 환경기술, ESG 관련 혁신기업들의 기술 수준과 사업 모델의 지속가능성을 평가하는 프로젝트입니다.",
        deadline: getRandomDate(30, 5),
        created_by: adminUser.id,
        created_at: new Date(),
        is_active: true,
        total_companies: 0,
        total_evaluations: 0,
        completed_evaluations: 0
    }
];

// 프로젝트 삽입
print("프로젝트 데이터 삽입 중...");
for (const project of sampleProjects) {
    try {
        db.projects.insertOne(project);
        print(`프로젝트 생성: ${project.name}`);
    } catch (error) {
        print(`프로젝트 생성 실패: ${project.name} - ${error.message}`);
    }
}// 각 프로젝트별 샘플 회사 데이터 생성
const companyTemplates = [
    // IT 기업들 (첫 번째 프로젝트용)
    [
        {
            name: "(주)테크이노베이션",
            business_number: "123-45-67890",
            address: "서울특별시 강남구 테헤란로 123",
            industry: "AI/머신러닝"
        },
        {
            name: "클라우드솔루션즈",
            business_number: "234-56-78901",
            address: "서울특별시 서초구 효령로 456",
            industry: "클라우드 서비스"
        },
        {
            name: "(주)모바일플랫폼",
            business_number: "345-67-89012",
            address: "경기도 성남시 분당구 정자일로 789",
            industry: "모바일 앱 개발"
        },
        {
            name: "사이버시큐리티코리아",
            business_number: "456-78-90123",
            address: "서울특별시 금천구 가산디지털1로 321",
            industry: "사이버보안"
        },
        {
            name: "(주)빅데이터랩",
            business_number: "567-89-01234",
            address: "서울특별시 중구 세종대로 654",
            industry: "빅데이터 분석"
        }
    ],    // 바이오헬스케어 기업들 (두 번째 프로젝트용)
    [
        {
            name: "(주)바이오메디컬",
            business_number: "678-90-12345",
            address: "경기도 수원시 영통구 월드컵로 111",
            industry: "바이오의약품"
        },
        {
            name: "메디테크솔루션",
            business_number: "789-01-23456",
            address: "서울특별시 송파구 올림픽로 222",
            industry: "의료기기"
        },
        {
            name: "(주)디지털헬스",
            business_number: "890-12-34567",
            address: "대전광역시 유성구 대학로 333",
            industry: "디지털헬스케어"
        },
        {
            name: "바이오진단연구소",
            business_number: "901-23-45678",
            address: "부산광역시 해운대구 센텀중앙로 444",
            industry: "체외진단기기"
        }
    ],
    // 그린테크 기업들 (세 번째 프로젝트용)
    [
        {
            name: "(주)그린에너지텍",
            business_number: "012-34-56789",
            address: "울산광역시 중구 종가로 555",
            industry: "태양광 발전"
        },
        {
            name: "스마트그리드코리아",
            business_number: "123-45-67891",
            address: "광주광역시 북구 첨단과기로 666",
            industry: "에너지 저장"
        },
        {
            name: "(주)환경기술개발",
            business_number: "234-56-78902",
            address: "대구광역시 달서구 성서공단로 777",
            industry: "환경정화기술"
        }
    ]
];// 회사 데이터 삽입 및 프로젝트별 회사 수 업데이트
print("\n회사 데이터 삽입 중...");
sampleProjects.forEach((project, projectIndex) => {
    const companies = companyTemplates[projectIndex];
    let companyCount = 0;
    
    companies.forEach(companyTemplate => {
        const company = {
            id: generateUUID(),
            name: companyTemplate.name,
            business_number: companyTemplate.business_number,
            address: companyTemplate.address,
            project_id: project.id,
            files: [],
            created_at: new Date(),
            evaluation_status: "pending",
            industry: companyTemplate.industry
        };
        
        try {
            db.companies.insertOne(company);
            companyCount++;
            print(`  회사 생성: ${company.name} (${company.industry})`);
        } catch (error) {
            print(`  회사 생성 실패: ${company.name} - ${error.message}`);
        }
    });
    
    // 프로젝트의 총 회사 수 업데이트
    db.projects.updateOne(
        { id: project.id },
        { 
            $set: { 
                total_companies: companyCount,
                total_evaluations: companyCount * evaluators.length
            }
        }
    );
    
    print(`프로젝트 "${project.name}": ${companyCount}개 회사 등록`);
});

// 결과 요약
const projectCount = db.projects.countDocuments();
const companyCount = db.companies.countDocuments();

print("\n=== 샘플 데이터 생성 완료 ===");
print(`총 프로젝트 수: ${projectCount}`);
print(`총 회사 수: ${companyCount}`);

// 생성된 데이터 검증
print("\n=== 데이터 검증 ===");
const projects = db.projects.find({}).toArray();
projects.forEach(project => {
    const companyCount = db.companies.countDocuments({ project_id: project.id });
    print(`${project.name}: ${companyCount}개 회사`);
});

print("\n스크립트 실행 완료!");