#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
온라인 평가 시스템 종합 기능 테스트
모든 주요 기능을 체계적으로 테스트합니다.
"""

import requests
import json
import time
import os
from datetime import datetime
from pathlib import Path

# 테스트 설정
BASE_URL = "http://localhost:8080"
TEST_RESULTS = []

class TestRunner:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.test_user = None
        self.results = []
    
    def log_result(self, test_name, success, message="", details=None):
        """테스트 결과 로깅"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        print(f"{status} | {test_name}")
        if message:
            print(f"    💬 {message}")
        if details and not success:
            print(f"    🔍 Details: {details}")
    
    def test_container_status(self):
        """도커 컨테이너 상태 확인"""
        print("\n🐳 도커 컨테이너 상태 확인")
        print("-" * 50)
        
        try:
            # 서버 응답 확인
            response = requests.get(f"{self.base_url}/", timeout=10)
            self.log_result("컨테이너 응답", response.status_code == 200, 
                          f"HTTP 상태 코드: {response.status_code}")
            
            # API 문서 접근 확인
            response = requests.get(f"{self.base_url}/docs", timeout=10)
            self.log_result("API 문서 접근", response.status_code == 200,
                          "Swagger UI 접근 가능")
            
            # 헬스 체크 (만약 있다면)
            try:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                self.log_result("헬스 체크", response.status_code == 200,
                              "헬스 체크 엔드포인트 응답")
            except:
                self.log_result("헬스 체크", False, "헬스 체크 엔드포인트 없음")
                
        except Exception as e:
            self.log_result("컨테이너 연결", False, f"연결 실패: {str(e)}")
    
    def test_user_management(self):
        """사용자 관리 기능 테스트"""
        print("\n👤 사용자 관리 기능 테스트")
        print("-" * 50)
        
        # 사용자 등록 테스트
        timestamp = int(time.time())
        self.test_user = {
            "username": f"test_comprehensive_{timestamp}",
            "email": f"test_comprehensive_{timestamp}@example.com",
            "password": "TestPass123!",
            "role": "evaluator",
            "company": "종합테스트 회사"
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/auth/register", 
                                   json=self.test_user, timeout=10)
            
            if response.status_code in [200, 201]:
                self.log_result("사용자 등록", True, "새 사용자 등록 성공")
            elif response.status_code == 400:
                # 이미 존재하는 사용자일 수 있음
                data = response.json()
                if "already exists" in str(data).lower():
                    self.log_result("사용자 등록", True, "사용자 이미 존재 (정상)")
                else:
                    self.log_result("사용자 등록", False, f"등록 실패: {data}")
            else:
                self.log_result("사용자 등록", False, 
                              f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("사용자 등록", False, f"요청 실패: {str(e)}")
        
        # 로그인 테스트
        try:
            login_data = {
                "username": self.test_user["username"],
                "password": self.test_user["password"]
            }
            
            response = requests.post(f"{self.base_url}/api/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                if self.token:
                    self.log_result("사용자 로그인", True, "토큰 발급 성공")
                else:
                    self.log_result("사용자 로그인", False, "토큰이 응답에 없음")
            else:
                self.log_result("사용자 로그인", False, 
                              f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("사용자 로그인", False, f"요청 실패: {str(e)}")
    
    def test_template_management(self):
        """템플릿 관리 기능 테스트"""
        print("\n📝 템플릿 관리 기능 테스트")
        print("-" * 50)
        
        if not self.token:
            self.log_result("템플릿 테스트", False, "인증 토큰이 없음")
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 템플릿 목록 조회
        try:
            response = requests.get(f"{self.base_url}/api/templates", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                templates = response.json()
                self.log_result("템플릿 목록 조회", True, 
                              f"{len(templates)}개 템플릿 발견")
            else:
                self.log_result("템플릿 목록 조회", False, 
                              f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("템플릿 목록 조회", False, f"요청 실패: {str(e)}")
        
        # 새 템플릿 생성 테스트
        new_template = {
            "name": f"종합테스트 템플릿 {int(time.time())}",
            "description": "자동 테스트로 생성된 템플릿",
            "criteria": [
                {
                    "name": "기술적 역량",
                    "description": "기술적 능력 평가",
                    "weight": 40,
                    "max_score": 5
                },
                {
                    "name": "의사소통",
                    "description": "커뮤니케이션 능력",
                    "weight": 30,
                    "max_score": 5
                },
                {
                    "name": "팀워크",
                    "description": "팀 협업 능력",
                    "weight": 30,
                    "max_score": 5
                }
            ]
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/templates", 
                                   json=new_template, headers=headers, timeout=10)
            
            if response.status_code in [200, 201]:
                self.log_result("템플릿 생성", True, "새 템플릿 생성 성공")
            else:
                self.log_result("템플릿 생성", False, 
                              f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("템플릿 생성", False, f"요청 실패: {str(e)}")
    
    def test_evaluation_management(self):
        """평가 관리 기능 테스트"""
        print("\n📊 평가 관리 기능 테스트")
        print("-" * 50)
        
        if not self.token:
            self.log_result("평가 테스트", False, "인증 토큰이 없음")
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 평가 목록 조회
        try:
            response = requests.get(f"{self.base_url}/api/evaluations", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                evaluations = response.json()
                self.log_result("평가 목록 조회", True, 
                              f"{len(evaluations)}개 평가 발견")
            else:
                self.log_result("평가 목록 조회", False, 
                              f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("평가 목록 조회", False, f"요청 실패: {str(e)}")
        
        # 평가 할당 목록 조회
        try:
            response = requests.get(f"{self.base_url}/api/evaluation-assignments", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                assignments = response.json()
                self.log_result("평가 할당 조회", True, 
                              f"{len(assignments)}개 할당 발견")
            else:
                self.log_result("평가 할당 조회", False, 
                              f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("평가 할당 조회", False, f"요청 실패: {str(e)}")
    
    def test_analytics_features(self):
        """분석 기능 테스트"""
        print("\n📈 분석 기능 테스트")
        print("-" * 50)
        
        if not self.token:
            self.log_result("분석 테스트", False, "인증 토큰이 없음")
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 대시보드 데이터 조회
        try:
            response = requests.get(f"{self.base_url}/api/analytics/dashboard", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                dashboard_data = response.json()
                self.log_result("대시보드 데이터", True, 
                              f"대시보드 데이터 조회 성공")
            else:
                self.log_result("대시보드 데이터", False, 
                              f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("대시보드 데이터", False, f"요청 실패: {str(e)}")
        
        # 진행 상황 통계 조회
        try:
            response = requests.get(f"{self.base_url}/api/analytics/progress", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                progress_data = response.json()
                self.log_result("진행 상황 통계", True, 
                              f"진행 상황 데이터 조회 성공")
            else:
                self.log_result("진행 상황 통계", False, 
                              f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("진행 상황 통계", False, f"요청 실패: {str(e)}")
    
    def test_export_functionality(self):
        """내보내기 기능 테스트"""
        print("\n📄 내보내기 기능 테스트")
        print("-" * 50)
        
        if not self.token:
            self.log_result("내보내기 테스트", False, "인증 토큰이 없음")
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 내보내기 가능한 평가 목록 조회
        try:
            response = requests.get(f"{self.base_url}/api/evaluations/export-list", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                export_list = response.json()
                self.log_result("내보내기 목록", True, 
                              f"{len(export_list)}개 내보내기 가능한 평가")
                
                # 내보내기 가능한 평가가 있으면 실제 내보내기 테스트
                if export_list:
                    eval_id = export_list[0]["id"]
                    
                    # PDF 내보내기 테스트
                    try:
                        response = requests.get(
                            f"{self.base_url}/api/evaluations/{eval_id}/export",
                            headers=headers,
                            params={"format": "pdf"},
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            self.log_result("PDF 내보내기", True, 
                                          f"PDF 파일 생성 성공 ({len(response.content)} bytes)")
                        else:
                            self.log_result("PDF 내보내기", False, 
                                          f"HTTP {response.status_code}")
                            
                    except Exception as e:
                        self.log_result("PDF 내보내기", False, f"요청 실패: {str(e)}")
                    
                    # Excel 내보내기 테스트
                    try:
                        response = requests.get(
                            f"{self.base_url}/api/evaluations/{eval_id}/export",
                            headers=headers,
                            params={"format": "excel"},
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            self.log_result("Excel 내보내기", True, 
                                          f"Excel 파일 생성 성공 ({len(response.content)} bytes)")
                        else:
                            self.log_result("Excel 내보내기", False, 
                                          f"HTTP {response.status_code}")
                            
                    except Exception as e:
                        self.log_result("Excel 내보내기", False, f"요청 실패: {str(e)}")
                else:
                    self.log_result("개별 내보내기", False, "내보내기 가능한 평가가 없음")
            else:
                self.log_result("내보내기 목록", False, 
                              f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("내보내기 목록", False, f"요청 실패: {str(e)}")
        
        # 대량 내보내기 테스트
        try:
            bulk_export_data = {
                "evaluation_ids": [],  # 빈 배열로 테스트
                "format": "excel",
                "export_type": "individual"
            }
            
            response = requests.post(
                f"{self.base_url}/api/evaluations/bulk-export",
                json=bulk_export_data,
                headers=headers,
                timeout=30
            )
            
            # 빈 배열이므로 400 에러가 정상
            if response.status_code in [200, 400]:
                self.log_result("대량 내보내기", True, 
                              "대량 내보내기 엔드포인트 응답")
            else:
                self.log_result("대량 내보내기", False, 
                              f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("대량 내보내기", False, f"요청 실패: {str(e)}")
    
    def test_file_structure(self):
        """파일 구조 확인"""
        print("\n📁 파일 구조 확인")
        print("-" * 50)
        
        required_files = [
            "backend/server.py",
            "backend/export_utils.py",
            "backend/requirements.txt",
            "frontend/src/App.js",
            "frontend/package.json",
            "docker-compose.yml",
            "README.md",
            "README_KR.md"
        ]
        
        for file_path in required_files:
            exists = Path(file_path).exists()
            self.log_result(f"파일 존재: {file_path}", exists)
    
    def test_korean_features(self):
        """한글 지원 기능 테스트"""
        print("\n🇰🇷 한글 지원 기능 테스트")
        print("-" * 50)
        
        # export_utils.py에서 한글 폰트 지원 확인
        try:
            export_utils_path = Path("backend/export_utils.py")
            if export_utils_path.exists():
                with open(export_utils_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                korean_features = [
                    ("Korean", "한글 폰트 등록"),
                    ("malgun.ttf", "맑은 고딕 폰트"),
                    ("KoreanTitle", "한글 제목 스타일"),
                    ("KoreanNormal", "한글 본문 스타일"),
                    ("utf-8", "UTF-8 인코딩")
                ]
                
                for feature, description in korean_features:
                    found = feature in content
                    self.log_result(f"한글 지원: {description}", found)
            else:
                self.log_result("한글 지원 파일", False, "export_utils.py 없음")
                
        except Exception as e:
            self.log_result("한글 지원 확인", False, f"파일 읽기 실패: {str(e)}")
    
    def generate_report(self):
        """테스트 결과 보고서 생성"""
        print("\n" + "=" * 70)
        print("📊 종합 테스트 결과 보고서")
        print("=" * 70)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"🕐 테스트 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 테스트 대상: {self.base_url}")
        print(f"📈 전체 테스트: {total_tests}개")
        print(f"✅ 성공: {passed_tests}개")
        print(f"❌ 실패: {failed_tests}개")
        print(f"📊 성공률: {success_rate:.1f}%")
        
        print(f"\n📋 카테고리별 결과:")
        categories = {}
        for result in self.results:
            category = result["test"].split()[0] if " " in result["test"] else "기타"
            if category not in categories:
                categories[category] = {"total": 0, "passed": 0}
            categories[category]["total"] += 1
            if result["success"]:
                categories[category]["passed"] += 1
        
        for category, stats in categories.items():
            rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"   {category}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")
        
        print(f"\n🎯 시스템 상태 평가:")
        if success_rate >= 95:
            print("🌟 우수: 시스템이 완벽하게 작동합니다!")
        elif success_rate >= 85:
            print("👍 양호: 시스템이 잘 작동하지만 몇 가지 개선점이 있습니다.")
        elif success_rate >= 70:
            print("⚠️ 보통: 시스템에 일부 문제가 있어 주의가 필요합니다.")
        else:
            print("🚨 주의: 시스템에 심각한 문제가 있어 즉시 점검이 필요합니다.")
        
        # 실패한 테스트 상세 정보
        failed_results = [r for r in self.results if not r["success"]]
        if failed_results:
            print(f"\n❌ 실패한 테스트 상세:")
            for result in failed_results:
                print(f"   • {result['test']}: {result['message']}")
        
        print(f"\n🔗 추가 정보:")
        print(f"   • 웹 인터페이스: {self.base_url}")
        print(f"   • API 문서: {self.base_url}/docs")
        print(f"   • GitHub README: 한글/영문 버전 모두 제공")
        
        # 보고서를 파일로 저장
        try:
            report_data = {
                "timestamp": datetime.now().isoformat(),
                "base_url": self.base_url,
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": success_rate
                },
                "categories": categories,
                "results": self.results
            }
            
            with open("comprehensive_test_report.json", "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 상세 보고서가 'comprehensive_test_report.json'에 저장되었습니다.")
            
        except Exception as e:
            print(f"\n❌ 보고서 저장 실패: {str(e)}")
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🧪 온라인 평가 시스템 종합 기능 테스트 시작")
        print("=" * 70)
        
        # 테스트 순서대로 실행
        self.test_container_status()
        self.test_file_structure()
        self.test_korean_features()
        self.test_user_management()
        self.test_template_management()
        self.test_evaluation_management()
        self.test_analytics_features()
        self.test_export_functionality()
        
        # 결과 보고서 생성
        self.generate_report()

def main():
    """메인 실행 함수"""
    runner = TestRunner()
    runner.run_all_tests()

if __name__ == "__main__":
    main()
