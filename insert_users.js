db.users.insertMany([
  {
    user_id: "admin",
    user_name: "관리자", 
    hashed_password: "$2b$12$9w7CEEFJUvV5XzAlXPff5ORl.5iY/znopsk9zdXmQBJBho9ziG1Ta",
    role: "admin",
    email: "admin@example.com",
    phone: "010-1111-2222",
    created_at: new Date()
  },
  {
    user_id: "secretary01",
    user_name: "간사01",
    hashed_password: "$2b$12$.F6azkpJ0119SV7OPEr74Of9u43Zre/T4yliuagUvOEJBsrgjJjw6",
    role: "secretary", 
    email: "secretary01@example.com",
    phone: "010-2222-3333",
    created_at: new Date()
  },
  {
    user_id: "evaluator01",
    user_name: "평가위원01",
    hashed_password: "$2b$12$q1hNwZv00UbDub6vCbb46OXlSnEhae/KRYx3Y8mbZ3vPf0xwjkMYq",
    role: "evaluator",
    email: "evaluator01@example.com", 
    phone: "010-3333-4444",
    created_at: new Date()
  }
]);
