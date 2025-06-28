/**
 * 온라인 평가 시스템 - 평가 템플릿 및 평가 시트 데이터 생성 스크립트
 * 실행: mongosh -u admin -p password123 --authenticationDatabase admin online_evaluation --file create_evaluation_data.js
 */

// 데이터베이스 연결
use('online_evaluation');

// UUID 생성 함수
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// 기존 데이터 조회
const existingUsers = db.users.find({}).toArray();
const existingProjects = db.projects.find({}).toArray();
const existingCompanies = db.companies.find({}).toArray();

const adminUser = existingUsers.find(user => user.role === 'admin');
const evaluators = existingUsers.filter(user => user.role === 'evaluator');

if (!adminUser || existingProjects.length === 0) {
    print("오류: 필요한 기본 데이터가 없습니다.");
    quit(1);
}

print(`기본 데이터 확인: 프로젝트(${existingProjects.length}), 회사(${existingCompanies.length}), 평가자(${evaluators.length})`);

// 평가 항목 템플릿
const evaluationItemTemplates = {
    tech: [
        { name: "기술 혁신성", description: "기술의 창의성과 혁신 정도", max_score: 20, weight: 0.25 },
        { name: "기술적 완성도", description: "기술 개발의 완성도와 안정성", max_score: 20, weight: 0.20 },
        { name: "기술 경쟁력", description: "시장 내 기술의 경쟁 우위", max_score: 15, weight: 0.15 },
        { name: "특허 및 지적재산권", description: "보유한 특허와 지적재산권 현황", max_score: 10, weight: 0.10 }
    ],
    business: [
        { name: "시장성", description: "대상 시장의 규모와 성장 가능성", max_score: 20, weight: 0.20 },
        { name: "사업모델 타당성", description: "수익 모델의 현실성과 지속가능성", max_score: 15, weight: 0.15 },
        { name: "마케팅 전략", description: "마케팅 및 영업 전략의 효과성", max_score: 10, weight: 0.10 }
    ],
    management: [
        { name: "경영진 역량", description: "CEO 및 핵심 경영진의 전문성", max_score: 15, weight: 0.15 },
        { name: "조직 운영", description: "조직 구조와 운영 체계의 효율성", max_score: 10, weight: 0.10 },
        { name: "재무 건전성", description: "재무 상태와 자금 조달 능력", max_score: 15, weight: 0.15 }
    ]
};

// 각 프로젝트에 대한 평가 템플릿 생성
print("\n평가 템플릿 생성 중...");
const createdTemplates = [];

existingProjects.forEach(project => {
    // 각 프로젝트별로 종합 평가 템플릿 생성
    const items = [];
    
    // 모든 평가 항목을 하나의 템플릿에 통합
    Object.values(evaluationItemTemplates).forEach(categoryItems => {
        categoryItems.forEach(item => {
            items.push({
                id: generateUUID(),
                name: item.name,
                description: item.description,
                max_score: item.max_score,
                weight: item.weight,
                project_id: project.id
            });
        });
    });
    
    const template = {
        id: generateUUID(),
        name: `${project.name} 종합 평가 템플릿`,
        description: `${project.name}에 참여하는 기업들을 평가하기 위한 종합 평가 템플릿`,
        project_id: project.id,
        items: items,
        created_by: adminUser.id,
        created_at: new Date(),
        is_active: true,
        version: 1,
        version_created_at: new Date(),
        shared_with: [],
        status: "active",
        last_modified: new Date()
    };
    
    try {
        db.evaluation_templates.insertOne(template);
        createdTemplates.push(template);
        print(`템플릿 생성: ${template.name} (${template.items.length}개 항목)`);
    } catch (error) {
        print(`템플릿 생성 실패: ${template.name} - ${error.message}`);
    }
});

// 평가 시트 생성
print("\n평가 시트 생성 중...");
let totalSheets = 0;

existingProjects.forEach(project => {
    const projectCompanies = existingCompanies.filter(company => company.project_id === project.id);
    const projectTemplate = createdTemplates.find(template => template.project_id === project.id);
    
    if (!projectTemplate) {
        print(`경고: 프로젝트 ${project.name}의 템플릿을 찾을 수 없습니다.`);
        return;
    }
    
    projectCompanies.forEach(company => {
        evaluators.forEach(evaluator => {
            const sheet = {
                id: generateUUID(),
                evaluator_id: evaluator.id,
                company_id: company.id,
                project_id: project.id,
                template_id: projectTemplate.id,
                status: "draft",
                deadline: project.deadline,
                created_at: new Date(),
                last_modified: new Date()
            };
            
            try {
                db.evaluation_sheets.insertOne(sheet);
                totalSheets++;
            } catch (error) {
                print(`시트 생성 실패: ${error.message}`);
            }
        });
    });
    
    print(`프로젝트 "${project.name}": ${projectCompanies.length}개 회사 × ${evaluators.length}명 평가자 = ${projectCompanies.length * evaluators.length}개 시트`);
});

// 일부 평가 시트에 샘플 점수 데이터 추가 (시연용)
print("\n샘플 평가 점수 생성 중...");
const sampleSheets = db.evaluation_sheets.find({ status: "draft" }).limit(3).toArray();

sampleSheets.forEach((sheet, index) => {
    const template = createdTemplates.find(t => t.id === sheet.template_id);
    if (!template) return;
    
    let totalScore = 0;
    let weightedScore = 0;
    
    template.items.forEach(item => {
        // 랜덤한 점수 생성 (실제 평가를 시뮬레이션)
        const score = Math.floor(Math.random() * (item.max_score * 0.4)) + (item.max_score * 0.6); // 60-100% 범위
        totalScore += score;
        weightedScore += score * item.weight;
        
        const scoreData = {
            id: generateUUID(),
            sheet_id: sheet.id,
            item_id: item.id,
            score: score,
            opinion: `${item.name}에 대한 평가 의견입니다. 점수: ${score}/${item.max_score}`,
            created_at: new Date()
        };
        
        try {
            db.evaluation_scores.insertOne(scoreData);
        } catch (error) {
            print(`점수 생성 실패: ${error.message}`);
        }
    });
    
    // 시트 상태 업데이트
    db.evaluation_sheets.updateOne(
        { id: sheet.id },
        { 
            $set: { 
                status: "submitted",
                submitted_at: new Date(),
                total_score: totalScore,
                weighted_score: weightedScore
            }
        }
    );
    
    print(`  샘플 시트 ${index + 1}: ${template.items.length}개 항목 평가 완료 (총점: ${totalScore.toFixed(1)})`);
});

// 결과 요약
const templateCount = db.evaluation_templates.countDocuments();
const sheetCount = db.evaluation_sheets.countDocuments();
const scoreCount = db.evaluation_scores.countDocuments();

print("\n=== 평가 데이터 생성 완료 ===");
print(`총 평가 템플릿: ${templateCount}개`);
print(`총 평가 시트: ${sheetCount}개`);
print(`총 평가 점수: ${scoreCount}개`);

// 데이터 검증
print("\n=== 데이터 검증 ===");
existingProjects.forEach(project => {
    const projectSheets = db.evaluation_sheets.countDocuments({ project_id: project.id });
    const submittedSheets = db.evaluation_sheets.countDocuments({ 
        project_id: project.id, 
        status: "submitted" 
    });
    print(`${project.name}: ${projectSheets}개 시트 (제출완료: ${submittedSheets}개)`);
});

print("\n스크립트 실행 완료!");
