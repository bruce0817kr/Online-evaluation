#!/usr/bin/env python3
"""
ELK Stack 기본 상태 검증 스크립트
Online Evaluation System - ELK Stack Basic Validation
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any

class ELKBasicValidator:
    def __init__(self):
        self.elasticsearch_url = "http://localhost:9200"
        self.kibana_url = "http://localhost:5601"
        self.logstash_url = "http://localhost:9600"
        self.results = {}
        
    def check_elasticsearch(self) -> Dict[str, Any]:
        """Elasticsearch 기본 상태 확인"""
        print("🔍 Elasticsearch 상태 확인 중...")
        try:
            # 클러스터 상태 확인
            response = requests.get(f"{self.elasticsearch_url}/_cluster/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                print(f"  ✅ Elasticsearch 연결 성공")
                print(f"  📊 클러스터 상태: {health.get('status', 'unknown')}")
                print(f"  🏥 노드 수: {health.get('number_of_nodes', 0)}")
                
                # 인덱스 목록 확인
                indices_response = requests.get(f"{self.elasticsearch_url}/_cat/indices?format=json", timeout=5)
                if indices_response.status_code == 200:
                    indices = indices_response.json()
                    app_logs_indices = [idx for idx in indices if idx.get('index', '').startswith('app-logs')]
                    print(f"  📁 애플리케이션 로그 인덱스: {len(app_logs_indices)}개")
                
                return {"status": "healthy", "details": health}
            else:
                print(f"  ❌ Elasticsearch 응답 오류: {response.status_code}")
                return {"status": "error", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"  ❌ Elasticsearch 연결 실패: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def check_logstash(self) -> Dict[str, Any]:
        """Logstash 기본 상태 확인"""
        print("\n🔍 Logstash 상태 확인 중...")
        try:
            response = requests.get(f"{self.logstash_url}", timeout=5)
            if response.status_code == 200:
                status = response.json()
                print(f"  ✅ Logstash 연결 성공")
                print(f"  📊 상태: {status.get('status', 'unknown')}")
                return {"status": "healthy", "details": status}
            else:
                print(f"  ❌ Logstash 응답 오류: {response.status_code}")
                return {"status": "error", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"  ❌ Logstash 연결 실패: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def check_kibana(self) -> Dict[str, Any]:
        """Kibana 기본 상태 확인"""
        print("\n🔍 Kibana 상태 확인 중...")
        try:
            response = requests.get(f"{self.kibana_url}/api/status", timeout=10)
            if response.status_code == 200:
                status = response.json()
                print(f"  ✅ Kibana 연결 성공")
                overall_status = status.get('status', {}).get('overall', {}).get('state', 'unknown')
                print(f"  📊 전체 상태: {overall_status}")
                return {"status": "healthy", "details": status}
            else:
                print(f"  ❌ Kibana 응답 오류: {response.status_code}")
                return {"status": "error", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"  ❌ Kibana 연결 실패: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def test_log_ingestion(self) -> Dict[str, Any]:
        """로그 수집 테스트"""
        print("\n🔍 로그 수집 테스트 중...")
        try:
            # 테스트 로그 생성
            test_log = {
                "@timestamp": datetime.utcnow().isoformat() + "Z",
                "level": "INFO",
                "message": "ELK Stack validation test log",
                "service": {
                    "name": "elk-validation-test",
                    "version": "1.0.0"
                },
                "test": True,
                "validation_id": f"test-{int(time.time())}"
            }
            
            # Elasticsearch에 직접 테스트 로그 전송
            index_name = f"app-logs-test-{datetime.now().strftime('%Y.%m.%d')}"
            response = requests.post(
                f"{self.elasticsearch_url}/{index_name}/_doc",
                json=test_log,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                print(f"  ✅ 테스트 로그 인덱싱 성공")
                print(f"  📁 인덱스: {index_name}")
                return {"status": "success", "index": index_name, "log": test_log}
            else:
                print(f"  ❌ 테스트 로그 인덱싱 실패: {response.status_code}")
                return {"status": "error", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"  ❌ 로그 수집 테스트 실패: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def check_ilm_policies(self) -> Dict[str, Any]:
        """ILM 정책 확인"""
        print("\n🔍 ILM 정책 확인 중...")
        try:
            response = requests.get(f"{self.elasticsearch_url}/_ilm/policy", timeout=5)
            if response.status_code == 200:
                policies = response.json()
                app_policies = [name for name in policies.keys() if 'app-logs' in name]
                print(f"  ✅ ILM 정책 확인 성공")
                print(f"  📋 애플리케이션 로그 정책: {len(app_policies)}개")
                for policy in app_policies:
                    print(f"    • {policy}")
                return {"status": "success", "policies": app_policies}
            else:
                print(f"  ❌ ILM 정책 확인 실패: {response.status_code}")
                return {"status": "error", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"  ❌ ILM 정책 확인 실패: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def run_validation(self) -> Dict[str, Any]:
        """전체 검증 실행"""
        print("🚀 ELK Stack 검증 시작...")
        print("=" * 60)
        
        # 각 컴포넌트 검증
        self.results['elasticsearch'] = self.check_elasticsearch()
        self.results['logstash'] = self.check_logstash()
        self.results['kibana'] = self.check_kibana()
        self.results['log_ingestion'] = self.test_log_ingestion()
        self.results['ilm_policies'] = self.check_ilm_policies()
        
        # 전체 상태 평가
        healthy_count = sum(1 for result in self.results.values() 
                          if result.get('status') in ['healthy', 'success'])
        total_checks = len(self.results)
        
        overall_status = "healthy" if healthy_count == total_checks else "degraded"
        
        # 결과 요약
        print("\n" + "=" * 60)
        print("📊 ELK Stack 검증 결과 요약")
        print("=" * 60)
        print(f"⏰ 검증 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🏥 전체 상태: {overall_status.upper()}")
        print(f"✅ 성공한 검사: {healthy_count}/{total_checks}")
        
        # 개별 결과
        status_icons = {
            'healthy': '✅',
            'success': '✅',
            'error': '❌',
            'degraded': '⚠️'
        }
        
        print(f"\n📋 개별 검사 결과:")
        for check_name, result in self.results.items():
            status = result.get('status', 'unknown')
            icon = status_icons.get(status, '❓')
            print(f"  {icon} {check_name.replace('_', ' ').title()}: {status}")
        
        # 권장사항
        if overall_status != "healthy":
            print(f"\n💡 권장사항:")
            for check_name, result in self.results.items():
                if result.get('status') == 'error':
                    print(f"  • {check_name} 서비스 상태를 확인하고 재시작해보세요")
        
        self.results['summary'] = {
            'overall_status': overall_status,
            'healthy_count': healthy_count,
            'total_checks': total_checks,
            'timestamp': datetime.now().isoformat()
        }
        
        return self.results
    
    def save_report(self, results: Dict[str, Any]) -> str:
        """검증 결과 저장"""
        report_file = f"elk_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n📁 상세 검증 리포트 저장: {report_file}")
        return report_file

def main():
    """메인 실행 함수"""
    validator = ELKBasicValidator()
    
    try:
        results = validator.run_validation()
        report_file = validator.save_report(results)
        
        # 최종 상태 코드 설정
        overall_status = results.get('summary', {}).get('overall_status', 'error')
        if overall_status == 'healthy':
            print(f"\n🎉 ELK Stack 검증 완료! 모든 시스템이 정상 작동 중입니다.")
            sys.exit(0)
        else:
            print(f"\n⚠️ ELK Stack에 일부 문제가 발견되었습니다. 상세 내용은 {report_file}을 확인하세요.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n👋 검증이 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 검증 중 오류가 발생했습니다: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
