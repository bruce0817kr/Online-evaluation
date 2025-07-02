// MongoDB 초기화 스크립트
// 데이터베이스 및 컬렉션 초기 설정

// 어플리케이션 데이터베이스 생성
db = db.getSiblingDB('online_evaluation');

// 컬렉션 생성 및 인덱스 설정
db.users.insertOne({
  login_id: "admin",
  name: "관리자",
  email: "admin@example.com",
  role: "admin",
  is_active: true,
  created_at: new Date(),
  updated_at: new Date()
});
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


