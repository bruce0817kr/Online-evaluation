// MongoDB 초기화 스크립트
// 데이터베이스 및 컬렉션 초기 설정

// 어플리케이션 데이터베이스 생성
db = db.getSiblingDB('online_evaluation');

// 사용자 생성
db.createUser({
  user: 'app_user',
  pwd: 'app_password123',
  roles: [
    {
      role: 'readWrite',
      db: 'online_evaluation'
    }
  ]
});

// 컬렉션 생성 및 인덱스 설정
db.createCollection('exams');
db.createCollection('submissions');
db.createCollection('users');
db.createCollection('results');

// 인덱스 생성 (성능 최적화)
db.exams.createIndex({ "exam_id": 1 }, { unique: true });
db.exams.createIndex({ "created_at": -1 });
db.exams.createIndex({ "status": 1 });

db.submissions.createIndex({ "submission_id": 1 }, { unique: true });
db.submissions.createIndex({ "exam_id": 1 });
db.submissions.createIndex({ "submitted_at": -1 });

db.users.createIndex({ "user_id": 1 }, { unique: true });
db.users.createIndex({ "email": 1 }, { unique: true });

db.results.createIndex({ "exam_id": 1, "user_id": 1 });
db.results.createIndex({ "calculated_at": -1 });

// 샘플 데이터 삽입 (선택사항)
db.exams.insertOne({
  exam_id: "sample_exam_001",
  title: "샘플 시험",
  description: "시스템 테스트용 샘플 시험입니다.",
  questions: [],
  time_limit: 60,
  total_score: 100,
  status: "active",
  created_at: new Date(),
  updated_at: new Date()
});

print("MongoDB 초기화 완료!");
print("- 데이터베이스: online_evaluation");
print("- 사용자: app_user");
print("- 컬렉션: exams, submissions, users, results");
print("- 인덱스 및 샘플 데이터 생성 완료");
