#!/usr/bin/env python3
"""
ELK Stack 성능 및 상태 모니터링 스크립트
Online Evaluation System - ELK Stack Performance Monitor
"""

import requests
import json
import time
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
import asyncio
import aiohttp

class ELKPerformanceMonitor:
    def __init__(self):
        self.elasticsearch_url = "http://localhost:9200"
        self.kibana_url = "http://localhost:5601"
        self.logstash_url = "http://localhost:9600"
        
    async def check_elasticsearch_health(self) -> Dict[str, Any]:
        """Elasticsearch 클러스터 상태 확인"""
        try:
            async with aiohttp.ClientSession() as session:
                # 클러스터 상태
                async with session.get(f"{self.elasticsearch_url}/_cluster/health") as resp:
                    cluster_health = await resp.json()
                
                # 노드 통계
                async with session.get(f"{self.elasticsearch_url}/_nodes/stats") as resp:
                    node_stats = await resp.json()
                
                # 인덱스 통계
                async with session.get(f"{self.elasticsearch_url}/_cat/indices?format=json") as resp:
                    indices_stats = await resp.json()
                
                return {
                    "status": "healthy" if cluster_health["status"] in ["green", "yellow"] else "unhealthy",
                    "cluster_health": cluster_health,
                    "node_stats": node_stats,
                    "indices_stats": indices_stats,
                    "timestamp": datetime.utcnow().isoformat()
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def check_logstash_health(self) -> Dict[str, Any]:
        """Logstash 상태 및 성능 확인"""
        try:
            async with aiohttp.ClientSession() as session:
                # Logstash 상태
                async with session.get(f"{self.logstash_url}") as resp:
                    logstash_status = await resp.json()
                
                # 파이프라인 통계
                async with session.get(f"{self.logstash_url}/_node/stats/pipelines") as resp:
                    pipeline_stats = await resp.json()
                
                return {
                    "status": "healthy" if logstash_status.get("status") == "green" else "unhealthy",
                    "logstash_status": logstash_status,
                    "pipeline_stats": pipeline_stats,
                    "timestamp": datetime.utcnow().isoformat()
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def check_kibana_health(self) -> Dict[str, Any]:
        """Kibana 상태 확인"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.kibana_url}/api/status") as resp:
                    kibana_status = await resp.json()
                
                return {
                    "status": "healthy" if kibana_status.get("status", {}).get("overall", {}).get("state") == "green" else "unhealthy",
                    "kibana_status": kibana_status,
                    "timestamp": datetime.utcnow().isoformat()
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def analyze_log_patterns(self) -> Dict[str, Any]:
        """로그 패턴 분석"""
        try:
            async with aiohttp.ClientSession() as session:
                # 최근 1시간 로그 분석
                query = {
                    "query": {
                        "range": {
                            "@timestamp": {
                                "gte": "now-1h"
                            }
                        }
                    },
                    "aggs": {
                        "log_levels": {
                            "terms": {
                                "field": "level",
                                "size": 10
                            }
                        },
                        "error_patterns": {
                            "filter": {
                                "term": {
                                    "level": "ERROR"
                                }
                            },
                            "aggs": {
                                "top_errors": {
                                    "terms": {
                                        "field": "error.type",
                                        "size": 5
                                    }
                                }
                            }
                        },
                        "performance_metrics": {
                            "stats": {
                                "field": "performance.duration"
                            }
                        },
                        "user_activity": {
                            "cardinality": {
                                "field": "user_id"
                            }
                        }
                    },
                    "size": 0
                }
                
                async with session.post(
                    f"{self.elasticsearch_url}/app-logs-*/_search",
                    json=query,
                    headers={"Content-Type": "application/json"}
                ) as resp:
                    search_results = await resp.json()
                
                return {
                    "status": "success",
                    "analysis": search_results.get("aggregations", {}),
                    "total_logs": search_results.get("hits", {}).get("total", {}).get("value", 0),
                    "timestamp": datetime.utcnow().isoformat()
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def check_index_performance(self) -> Dict[str, Any]:
        """인덱스 성능 분석"""
        try:
            async with aiohttp.ClientSession() as session:
                # 인덱스 크기 및 성능 통계
                async with session.get(f"{self.elasticsearch_url}/_cat/indices/app-logs-*?format=json&bytes=b") as resp:
                    indices_info = await resp.json()
                
                # 샤드 정보
                async with session.get(f"{self.elasticsearch_url}/_cat/shards/app-logs-*?format=json") as resp:
                    shards_info = await resp.json()
                
                performance_summary = {
                    "total_indices": len(indices_info),
                    "total_size_bytes": sum(int(idx.get("store.size", "0")) for idx in indices_info),
                    "total_docs": sum(int(idx.get("docs.count", "0")) for idx in indices_info),
                    "largest_index": max(indices_info, key=lambda x: int(x.get("store.size", "0")), default={}),
                    "indices_health": [
                        {
                            "index": idx["index"],
                            "health": idx["health"],
                            "size": idx.get("store.size", "0"),
                            "docs": idx.get("docs.count", "0")
                        }
                        for idx in indices_info
                    ]
                }
                
                return {
                    "status": "success",
                    "performance_summary": performance_summary,
                    "indices_details": indices_info,
                    "shards_details": shards_info,
                    "timestamp": datetime.utcnow().isoformat()
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def generate_performance_report(self) -> Dict[str, Any]:
        """종합 성능 리포트 생성"""
        print("🔍 ELK Stack 성능 모니터링 시작...")
        
        # 모든 검사를 병렬로 실행
        tasks = [
            self.check_elasticsearch_health(),
            self.check_logstash_health(),
            self.check_kibana_health(),
            self.analyze_log_patterns(),
            self.check_index_performance()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elasticsearch_health, logstash_health, kibana_health, log_analysis, index_performance = results
        
        # 전체 시스템 상태 평가
        overall_status = "healthy"
        if any(result.get("status") != "healthy" and result.get("status") != "success" 
               for result in results if isinstance(result, dict)):
            overall_status = "degraded"
        
        # 권장사항 생성
        recommendations = []
        
        if isinstance(elasticsearch_health, dict) and elasticsearch_health.get("status") == "healthy":
            cluster_health = elasticsearch_health.get("cluster_health", {})
            if cluster_health.get("number_of_pending_tasks", 0) > 0:
                recommendations.append("Elasticsearch has pending tasks - consider scaling resources")
        
        if isinstance(index_performance, dict) and index_performance.get("status") == "success":
            perf_summary = index_performance.get("performance_summary", {})
            if perf_summary.get("total_size_bytes", 0) > 50 * 1024 * 1024 * 1024:  # 50GB
                recommendations.append("Index size is large - consider implementing ILM policies")
        
        if isinstance(log_analysis, dict) and log_analysis.get("status") == "success":
            analysis = log_analysis.get("analysis", {})
            error_count = 0
            for bucket in analysis.get("log_levels", {}).get("buckets", []):
                if bucket.get("key") == "ERROR":
                    error_count = bucket.get("doc_count", 0)
            if error_count > 100:  # 1시간에 100개 이상 에러
                recommendations.append(f"High error rate detected: {error_count} errors in the last hour")
        
        report = {
            "overview": {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": overall_status,
                "recommendations": recommendations
            },
            "elasticsearch": elasticsearch_health if isinstance(elasticsearch_health, dict) else {"status": "error", "error": str(elasticsearch_health)},
            "logstash": logstash_health if isinstance(logstash_health, dict) else {"status": "error", "error": str(logstash_health)},
            "kibana": kibana_health if isinstance(kibana_health, dict) else {"status": "error", "error": str(kibana_health)},
            "log_analysis": log_analysis if isinstance(log_analysis, dict) else {"status": "error", "error": str(log_analysis)},
            "index_performance": index_performance if isinstance(index_performance, dict) else {"status": "error", "error": str(index_performance)}
        }
        
        return report
    
    def print_performance_summary(self, report: Dict[str, Any]):
        """성능 리포트 요약 출력"""
        print("\\n" + "="*80)
        print("🎯 ELK STACK 성능 모니터링 리포트")
        print("="*80)
        
        overview = report.get("overview", {})
        print(f"⏰ 실행 시간: {overview.get('timestamp', 'N/A')}")
        print(f"🏥 전체 상태: {overview.get('overall_status', 'unknown').upper()}")
        
        # 서비스별 상태
        print("\\n📊 서비스 상태:")
        services = ["elasticsearch", "logstash", "kibana"]
        for service in services:
            service_data = report.get(service, {})
            status = service_data.get("status", "unknown")
            emoji = "✅" if status in ["healthy", "success"] else "❌" if status == "error" else "⚠️"
            print(f"  {emoji} {service.title()}: {status}")
        
        # 로그 분석 요약
        log_analysis = report.get("log_analysis", {})
        if log_analysis.get("status") == "success":
            print("\\n📈 로그 분석 (최근 1시간):")
            print(f"  📄 총 로그 수: {log_analysis.get('total_logs', 0):,}")
            
            analysis = log_analysis.get("analysis", {})
            if "log_levels" in analysis:
                print("  📊 로그 레벨 분포:")
                for bucket in analysis["log_levels"].get("buckets", []):
                    level = bucket.get("key", "unknown")
                    count = bucket.get("doc_count", 0)
                    print(f"    • {level}: {count:,}")
            
            if "user_activity" in analysis:
                active_users = analysis["user_activity"].get("value", 0)
                print(f"  👥 활성 사용자: {active_users}")
        
        # 인덱스 성능 요약
        index_perf = report.get("index_performance", {})
        if index_perf.get("status") == "success":
            perf_summary = index_perf.get("performance_summary", {})
            print("\\n💾 인덱스 성능:")
            print(f"  📁 총 인덱스 수: {perf_summary.get('total_indices', 0)}")
            print(f"  📄 총 문서 수: {perf_summary.get('total_docs', 0):,}")
            total_size_mb = perf_summary.get('total_size_bytes', 0) / (1024 * 1024)
            print(f"  💿 총 크기: {total_size_mb:.2f} MB")
        
        # 권장사항
        recommendations = overview.get("recommendations", [])
        if recommendations:
            print("\\n💡 권장사항:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        print("\\n" + "="*80)

async def main():
    """메인 실행 함수"""
    monitor = ELKPerformanceMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--watch":
        # 지속적인 모니터링 모드
        print("🔄 지속적인 모니터링 모드 시작 (Ctrl+C로 종료)")
        try:
            while True:
                report = await monitor.generate_performance_report()
                monitor.print_performance_summary(report)
                print("\\n⏳ 5분 후 다시 확인...")
                await asyncio.sleep(300)  # 5분 대기
        except KeyboardInterrupt:
            print("\\n👋 모니터링을 종료합니다.")
    else:
        # 일회성 검사
        report = await monitor.generate_performance_report()
        monitor.print_performance_summary(report)
        
        # JSON 리포트 저장
        report_file = f"elk_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\\n📁 상세 리포트가 저장되었습니다: {report_file}")

if __name__ == "__main__":
    asyncio.run(main())
