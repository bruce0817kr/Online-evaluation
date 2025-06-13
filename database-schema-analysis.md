# 온라인 평가 시스템 MongoDB 컬렉션 스키마 분석

## 개요
백엔드 server.py의 Pydantic 모델들을 분석하여 MongoDB 컬렉션 구조를 정의합니다.

## 컬렉션 스키마 정의

### 1. users 컬렉션
```json
{
  "_id": "ObjectId",
  "id": "string (UUID)",
  "login_id": "string (unique)",
  "password_hash": "string",
  "user_name": "string", 
  "email": "string (unique)",
  "phone": "string (optional)",
  "role": "string (admin|secretary|evaluator)",
  "created_at": "datetime",
  "is_active": "boolean",
  "last_login": "datetime (optional)"
}
```

**인덱스:**
- `login_id`: unique
- `email`: unique
- `role`: 1 (역할별 조회)
- `is_active`: 1 (활성 사용자 조회)

### 2. projects 컬렉션
```json
{
  "_id": "ObjectId",
  "id": "string (UUID)",
  "name": "string",
  "description": "string",
  "deadline": "datetime",
  "created_by": "string (user_id)",
  "created_at": "datetime",
  "is_active": "boolean",
  "total_companies": "number",
  "total_evaluations": "number", 
  "completed_evaluations": "number"
}
```

**인덱스:**
- `id`: unique
- `created_by`: 1 (생성자별 조회)
- `is_active`: 1 (활성 프로젝트 조회)
- `deadline`: 1 (마감일별 정렬)

### 3. companies 컬렉션
```json
{
  "_id": "ObjectId",
  "id": "string (UUID)",
  "name": "string",
  "business_number": "string",
  "address": "string",
  "project_id": "string (UUID)",
  "files": [
    {
      "id": "string",
      "filename": "string", 
      "path": "string",
      "size": "number",
      "type": "string",
      "uploaded_at": "datetime"
    }
  ],
  "created_at": "datetime",
  "evaluation_status": "string (pending|in_progress|completed)"
}
```

**인덱스:**
- `id`: unique
- `project_id`: 1 (프로젝트별 회사 조회)
- `business_number`: 1 (사업자번호 조회)
- `evaluation_status`: 1 (평가 상태별 조회)

### 4. evaluation_templates 컬렉션
```json
{
  "_id": "ObjectId",
  "id": "string (UUID)",
  "name": "string",
  "description": "string",
  "project_id": "string (UUID)",
  "items": [
    {
      "id": "string (UUID)",
      "name": "string",
      "description": "string", 
      "max_score": "number",
      "weight": "number",
      "project_id": "string"
    }
  ],
  "created_by": "string (user_id)",
  "created_at": "datetime",
  "is_active": "boolean",
  "version": "number",
  "version_created_at": "datetime",
  "cloned_from": "string (template_id, optional)",
  "shared_with": [
    {
      "user_id": "string",
      "permission": "string (view|edit)"
    }
  ],
  "status": "string (draft|active|archived)",
  "last_modified": "datetime (optional)"
}
```

**인덱스:**
- `id`: unique
- `project_id`: 1 (프로젝트별 템플릿 조회)
- `created_by`: 1 (생성자별 조회)
- `status`: 1 (상태별 조회)
- `is_active`: 1 (활성 템플릿 조회)

### 5. evaluation_sheets 컬렉션
```json
{
  "_id": "ObjectId",
  "id": "string (UUID)",
  "evaluator_id": "string (user_id)",
  "company_id": "string (UUID)",
  "project_id": "string (UUID)",
  "template_id": "string (UUID)",
  "status": "string (draft|submitted|reviewed)",
  "deadline": "datetime (optional)",
  "created_at": "datetime",
  "submitted_at": "datetime (optional)",
  "last_modified": "datetime",
  "total_score": "number (optional)",
  "weighted_score": "number (optional)"
}
```

**인덱스:**
- `id`: unique
- `evaluator_id`: 1 (평가자별 시트 조회)
- `company_id`: 1 (회사별 평가 조회)
- `project_id`: 1 (프로젝트별 평가 조회)
- `template_id`: 1 (템플릿별 평가 조회)
- `status`: 1 (상태별 조회)
- compound: `{"evaluator_id": 1, "status": 1}` (평가자의 상태별 시트)

### 6. evaluation_scores 컬렉션
```json
{
  "_id": "ObjectId", 
  "id": "string (UUID)",
  "sheet_id": "string (UUID)",
  "item_id": "string (UUID)",
  "score": "number",
  "opinion": "string",
  "created_at": "datetime"
}
```

**인덱스:**
- `id`: unique
- `sheet_id`: 1 (시트별 점수 조회)
- `item_id`: 1 (항목별 점수 조회)
- compound: `{"sheet_id": 1, "item_id": 1}` (시트의 특정 항목 점수)

### 7. secretary_approvals 컬렉션
```json
{
  "_id": "ObjectId",
  "id": "string (UUID)",
  "name": "string",
  "phone": "string",
  "email": "string",
  "reason": "string",
  "status": "string (pending|approved|rejected)",
  "created_at": "datetime",
  "reviewed_at": "datetime (optional)",
  "reviewed_by": "string (user_id, optional)"
}
```

**인덱스:**
- `id`: unique
- `email`: unique
- `status`: 1 (상태별 조회)
- `created_at`: -1 (최신순 정렬)

### 8. file_metadata 컬렉션
```json
{
  "_id": "ObjectId",
  "id": "string (UUID)",
  "filename": "string",
  "original_filename": "string", 
  "file_path": "string",
  "file_size": "number",
  "file_type": "string",
  "uploaded_by": "string (user_id)",
  "uploaded_at": "datetime",
  "company_id": "string (UUID)",
  "is_processed": "boolean"
}
```

**인덱스:**
- `id`: unique
- `company_id`: 1 (회사별 파일 조회)
- `uploaded_by`: 1 (업로더별 파일 조회)
- `file_type`: 1 (파일 타입별 조회)
- `is_processed`: 1 (처리 상태별 조회)

## 컬렉션 간 관계

1. **users** → **projects** (created_by)
2. **projects** → **companies** (project_id)
3. **projects** → **evaluation_templates** (project_id)
4. **users** → **evaluation_sheets** (evaluator_id)
5. **companies** → **evaluation_sheets** (company_id)
6. **evaluation_templates** → **evaluation_sheets** (template_id)
7. **evaluation_sheets** → **evaluation_scores** (sheet_id)
8. **companies** → **file_metadata** (company_id)

## 성능 최적화 고려사항

1. **복합 인덱스**: 자주 함께 쿼리되는 필드들 조합
2. **텍스트 인덱스**: 검색 기능을 위한 name, description 필드
3. **TTL 인덱스**: 임시 데이터의 자동 만료 (필요시)
4. **Sparse 인덱스**: 선택적 필드에 대한 효율적 인덱싱

## 데이터 무결성 제약사항

1. **참조 무결성**: 관련 문서 삭제 시 연관 데이터 처리
2. **유니크 제약**: login_id, email 등 중복 방지
3. **필수 필드**: 각 모델의 required 필드 검증
4. **데이터 타입**: 문자열, 숫자, 날짜 등 적절한 타입 보장