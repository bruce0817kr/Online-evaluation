#!/usr/bin/env python3
"""
AI 모델 관리 시스템 - 데이터베이스 성능 테스트
MongoDB 성능 및 쿼리 최적화 분석
"""

import asyncio
import motor.motor_asyncio
import pymongo
import time
import statistics
from typing import Dict, List, Any
import logging
from datetime import datetime, timedelta
import random
import json
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv('.env.performance')

@dataclass
class DBPerformanceResult:
    """DB 성능 테스트 결과"""
    operation: str
    execution_times: List[float]
    documents_processed: int
    errors: List[str]
    avg_time: float
    max_time: float
    min_time: float

class DatabasePerformanceTest:
    """데이터베이스 성능 테스트 클래스"""
    
    def __init__(self):
        self.mongodb_url = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/online_evaluation_test')
        self.client = None
        self.db = None
        self.results: List[DBPerformanceResult] = []
        
        # 로깅 설정
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    async def setup_database(self):
        """데이터베이스 연결 설정"""
        self.client = motor.motor_asyncio.AsyncIOMotorClient(self.mongodb_url)
        self.db = self.client.get_default_database()
        
        # 연결 테스트
        try:
            await self.client.admin.command('ismaster')
            self.logger.info("MongoDB 연결 성공")
        except Exception as e:
            self.logger.error(f"MongoDB 연결 실패: {e}")
            raise
            
    async def cleanup_database(self):
        """데이터베이스 연결 정리"""
        if self.client:
            self.client.close()
            
    async def create_test_data(self, num_models: int = 1000):
        """테스트용 AI 모델 데이터 생성"""
        self.logger.info(f"테스트 데이터 생성 중: {num_models}개 모델")
        
        # 기존 테스트 데이터 정리
        await self.db.ai_models_test.delete_many({"model_id": {"$regex": "^test-"}})
        
        providers = ["openai", "anthropic", "google", "novita", "local"]
        model_names = ["gpt-3.5-turbo", "gpt-4", "claude-3-haiku", "claude-3-sonnet", 
                      "gemini-pro", "llama-2-70b", "custom-model"]
        
        test_models = []
        for i in range(num_models):
            provider = random.choice(providers)
            model_name = random.choice(model_names)
            
            model = {
                "model_id": f"test-model-{i:05d}",
                "provider": provider,
                "model_name": model_name,
                "display_name": f"Test Model {i}",
                "api_endpoint": f"https://api.{provider}.com/v1/chat/completions",
                "input_cost_per_token": round(random.uniform(0.0001, 0.01), 6),
                "output_cost_per_token": round(random.uniform(0.0002, 0.02), 6),
                "max_tokens": random.choice([2048, 4096, 8192, 16384]),
                "capabilities": random.sample([
                    "text-generation", "analysis", "korean", "evaluation", 
                    "multilingual", "coding", "reasoning"
                ], k=random.randint(2, 5)),
                "quality_score": round(random.uniform(0.5, 1.0), 2),
                "speed_score": round(random.uniform(0.3, 1.0), 2),
                "cost_efficiency": round(random.uniform(0.4, 1.0), 2),
                "reliability_score": round(random.uniform(0.6, 1.0), 2),
                "is_default": False,
                "is_active": random.choice([True, False]),
                "created_at": datetime.now() - timedelta(days=random.randint(1, 365)),
                "updated_at": datetime.now() - timedelta(days=random.randint(0, 30))
            }
            test_models.append(model)
            
        # 배치 삽입
        start_time = time.time()
        await self.db.ai_models_test.insert_many(test_models)
        end_time = time.time()
        
        self.logger.info(f"테스트 데이터 생성 완료: {end_time - start_time:.2f}초")
        
        # 인덱스 생성
        await self._create_indexes()
        
    async def _create_indexes(self):
        """성능 테스트를 위한 인덱스 생성"""
        self.logger.info("인덱스 생성 중...")
        
        indexes = [
            [("model_id", 1)],  # 단일 필드 인덱스
            [("provider", 1), ("is_active", 1)],  # 복합 인덱스
            [("quality_score", -1)],  # 내림차순 인덱스
            [("created_at", -1)],  # 시간 기반 인덱스
            [("capabilities", 1)],  # 배열 필드 인덱스
            [("display_name", "text")]  # 텍스트 인덱스
        ]
        
        for index in indexes:
            try:
                await self.db.ai_models_test.create_index(index)
            except Exception as e:
                self.logger.warning(f"인덱스 생성 실패: {index} - {e}")
                
    async def test_basic_operations(self) -> List[DBPerformanceResult]:
        """기본 CRUD 연산 성능 테스트"""
        results = []
        
        # 1. 단일 문서 조회 (인덱스 사용)
        result = await self._test_operation(
            "single_find_indexed",
            self._single_find_indexed,
            iterations=1000
        )
        results.append(result)
        
        # 2. 단일 문서 조회 (인덱스 미사용)
        result = await self._test_operation(
            "single_find_unindexed", 
            self._single_find_unindexed,
            iterations=100
        )
        results.append(result)
        
        # 3. 다중 문서 조회
        result = await self._test_operation(
            "multiple_find",
            self._multiple_find,
            iterations=100
        )
        results.append(result)
        
        # 4. 집계 파이프라인
        result = await self._test_operation(
            "aggregation_pipeline",
            self._aggregation_pipeline,
            iterations=50
        )
        results.append(result)
        
        # 5. 문서 삽입
        result = await self._test_operation(
            "document_insert",
            self._document_insert,
            iterations=100
        )
        results.append(result)
        
        # 6. 문서 업데이트
        result = await self._test_operation(
            "document_update",
            self._document_update,
            iterations=100
        )
        results.append(result)
        
        # 7. 문서 삭제
        result = await self._test_operation(
            "document_delete",
            self._document_delete,
            iterations=100
        )
        results.append(result)
        
        return results
        
    async def _test_operation(self, operation_name: str, operation_func, iterations: int) -> DBPerformanceResult:
        """개별 연산 성능 테스트"""
        self.logger.info(f"테스트 중: {operation_name} ({iterations}회)")
        
        execution_times = []
        errors = []
        documents_processed = 0
        
        for i in range(iterations):
            try:
                start_time = time.time()
                doc_count = await operation_func()
                end_time = time.time()
                
                execution_times.append((end_time - start_time) * 1000)  # ms
                documents_processed += doc_count
                
            except Exception as e:
                errors.append(f"Iteration {i}: {str(e)}")
                
        # 통계 계산
        if execution_times:
            avg_time = statistics.mean(execution_times)
            max_time = max(execution_times)
            min_time = min(execution_times)
        else:
            avg_time = max_time = min_time = 0
            
        return DBPerformanceResult(
            operation=operation_name,
            execution_times=execution_times,
            documents_processed=documents_processed,
            errors=errors,
            avg_time=avg_time,
            max_time=max_time,
            min_time=min_time
        )
        
    async def _single_find_indexed(self) -> int:
        """인덱스를 사용한 단일 문서 조회"""
        model_id = f"test-model-{random.randint(0, 999):05d}"
        doc = await self.db.ai_models_test.find_one({"model_id": model_id})
        return 1 if doc else 0
        
    async def _single_find_unindexed(self) -> int:
        """인덱스를 사용하지 않는 단일 문서 조회"""
        quality_score = round(random.uniform(0.5, 1.0), 2)
        doc = await self.db.ai_models_test.find_one({"quality_score": quality_score})
        return 1 if doc else 0
        
    async def _multiple_find(self) -> int:
        """다중 문서 조회"""
        provider = random.choice(["openai", "anthropic", "google", "novita"])
        cursor = self.db.ai_models_test.find({"provider": provider}).limit(50)
        docs = await cursor.to_list(length=50)
        return len(docs)
        
    async def _aggregation_pipeline(self) -> int:
        """집계 파이프라인 실행"""
        pipeline = [
            {"$match": {"is_active": True}},
            {"$group": {
                "_id": "$provider",
                "avg_quality": {"$avg": "$quality_score"},
                "avg_speed": {"$avg": "$speed_score"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"avg_quality": -1}}
        ]
        
        cursor = self.db.ai_models_test.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        return len(results)
        
    async def _document_insert(self) -> int:
        """문서 삽입"""
        doc = {
            "model_id": f"perf-test-{int(time.time() * 1000000)}",
            "provider": "test",
            "model_name": "performance-test-model",
            "display_name": "Performance Test Model",
            "quality_score": 0.8,
            "speed_score": 0.9,
            "cost_efficiency": 0.85,
            "reliability_score": 0.9,
            "is_active": True,
            "created_at": datetime.now()
        }
        
        result = await self.db.ai_models_test.insert_one(doc)
        return 1 if result.inserted_id else 0
        
    async def _document_update(self) -> int:
        """문서 업데이트"""
        model_id = f"test-model-{random.randint(0, 999):05d}"
        result = await self.db.ai_models_test.update_one(
            {"model_id": model_id},
            {"$set": {"updated_at": datetime.now(), "quality_score": random.uniform(0.5, 1.0)}}
        )
        return result.modified_count
        
    async def _document_delete(self) -> int:
        """문서 삭제 (테스트용 문서만)"""
        result = await self.db.ai_models_test.delete_one({"provider": "test"})
        return result.deleted_count
        
    async def test_concurrent_operations(self, concurrent_tasks: int = 10) -> List[DBPerformanceResult]:
        """동시 연산 성능 테스트"""
        self.logger.info(f"동시 연산 테스트: {concurrent_tasks}개 태스크")
        
        async def concurrent_read_task():
            """동시 읽기 태스크"""
            times = []
            for _ in range(10):
                start_time = time.time()
                await self._multiple_find()
                end_time = time.time()
                times.append((end_time - start_time) * 1000)
            return times
            
        async def concurrent_write_task():
            """동시 쓰기 태스크"""
            times = []
            for _ in range(5):
                start_time = time.time()
                await self._document_insert()
                end_time = time.time()
                times.append((end_time - start_time) * 1000)
            return times
            
        # 읽기 태스크 실행
        read_tasks = [concurrent_read_task() for _ in range(concurrent_tasks // 2)]
        write_tasks = [concurrent_write_task() for _ in range(concurrent_tasks // 2)]
        
        all_tasks = read_tasks + write_tasks
        results = await asyncio.gather(*all_tasks)
        
        # 결과 분석
        read_times = []
        write_times = []
        
        for i, result in enumerate(results):
            if i < len(read_tasks):
                read_times.extend(result)
            else:
                write_times.extend(result)
                
        concurrent_results = []
        
        if read_times:
            concurrent_results.append(DBPerformanceResult(
                operation="concurrent_reads",
                execution_times=read_times,
                documents_processed=len(read_times),
                errors=[],
                avg_time=statistics.mean(read_times),
                max_time=max(read_times),
                min_time=min(read_times)
            ))
            
        if write_times:
            concurrent_results.append(DBPerformanceResult(
                operation="concurrent_writes",
                execution_times=write_times,
                documents_processed=len(write_times),
                errors=[],
                avg_time=statistics.mean(write_times),
                max_time=max(write_times),
                min_time=min(write_times)
            ))
            
        return concurrent_results
        
    async def test_query_optimization(self) -> List[DBPerformanceResult]:
        """쿼리 최적화 테스트"""
        results = []
        
        # 1. 인덱스 효과 비교
        self.logger.info("인덱스 효과 비교 테스트")
        
        # 인덱스 사용 쿼리
        start_time = time.time()
        for _ in range(100):
            await self.db.ai_models_test.find_one({"model_id": f"test-model-{random.randint(0, 999):05d}"})
        indexed_time = time.time() - start_time
        
        # 인덱스 미사용 쿼리  
        start_time = time.time()
        for _ in range(100):
            await self.db.ai_models_test.find_one({"display_name": f"Test Model {random.randint(0, 999)}"})
        unindexed_time = time.time() - start_time
        
        results.append(DBPerformanceResult(
            operation="indexed_query_comparison",
            execution_times=[indexed_time * 1000, unindexed_time * 1000],
            documents_processed=200,
            errors=[],
            avg_time=(indexed_time + unindexed_time) * 500,
            max_time=max(indexed_time, unindexed_time) * 1000,
            min_time=min(indexed_time, unindexed_time) * 1000
        ))
        
        # 2. 프로젝션 효과 테스트
        self.logger.info("프로젝션 효과 테스트")
        
        # 전체 필드 조회
        start_time = time.time()
        cursor = self.db.ai_models_test.find({"provider": "openai"}).limit(100)
        await cursor.to_list(length=100)
        full_projection_time = time.time() - start_time
        
        # 일부 필드만 조회
        start_time = time.time()
        cursor = self.db.ai_models_test.find(
            {"provider": "openai"}, 
            {"model_id": 1, "display_name": 1, "quality_score": 1}
        ).limit(100)
        await cursor.to_list(length=100)
        partial_projection_time = time.time() - start_time
        
        results.append(DBPerformanceResult(
            operation="projection_comparison",
            execution_times=[full_projection_time * 1000, partial_projection_time * 1000],
            documents_processed=200,
            errors=[],
            avg_time=(full_projection_time + partial_projection_time) * 500,
            max_time=max(full_projection_time, partial_projection_time) * 1000,
            min_time=min(full_projection_time, partial_projection_time) * 1000
        ))
        
        return results
        
    def analyze_results(self, results: List[DBPerformanceResult]) -> Dict:
        """결과 분석"""
        analysis = {
            'summary': {
                'total_operations': len(results),
                'total_documents_processed': sum(r.documents_processed for r in results),
                'total_errors': sum(len(r.errors) for r in results),
                'avg_response_time': 0,
                'slowest_operation': '',
                'fastest_operation': ''
            },
            'operations': {},
            'recommendations': []
        }
        
        if not results:
            return analysis
            
        # 연산별 분석
        all_avg_times = []
        for result in results:
            analysis['operations'][result.operation] = {
                'avg_time': result.avg_time,
                'max_time': result.max_time,
                'min_time': result.min_time,
                'documents_processed': result.documents_processed,
                'error_count': len(result.errors),
                'throughput': result.documents_processed / (result.avg_time / 1000) if result.avg_time > 0 else 0
            }
            all_avg_times.append(result.avg_time)
            
        # 전체 평균
        if all_avg_times:
            analysis['summary']['avg_response_time'] = statistics.mean(all_avg_times)
            
            # 가장 느린/빠른 연산
            slowest = max(results, key=lambda x: x.avg_time)
            fastest = min(results, key=lambda x: x.avg_time)
            analysis['summary']['slowest_operation'] = f"{slowest.operation} ({slowest.avg_time:.2f}ms)"
            analysis['summary']['fastest_operation'] = f"{fastest.operation} ({fastest.avg_time:.2f}ms)"
            
        # 성능 개선 권장사항
        recommendations = []
        
        for result in results:
            if result.avg_time > 100:  # 100ms 초과
                recommendations.append(f"{result.operation}: 평균 응답시간이 {result.avg_time:.2f}ms로 느림 - 인덱스 최적화 필요")
                
            if len(result.errors) > 0:
                recommendations.append(f"{result.operation}: {len(result.errors)}개 에러 발생 - 에러 원인 분석 필요")
                
            if 'unindexed' in result.operation and result.avg_time > 50:
                recommendations.append(f"{result.operation}: 인덱스 미사용 쿼리 성능 저하 - 적절한 인덱스 생성 권장")
                
        analysis['recommendations'] = recommendations
        
        return analysis
        
    def generate_report(self, analysis: Dict) -> str:
        """DB 성능 테스트 리포트 생성"""
        report = []
        report.append("=" * 60)
        report.append("AI 모델 관리 시스템 - 데이터베이스 성능 테스트 리포트")
        report.append("=" * 60)
        report.append(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 전체 요약
        summary = analysis['summary']
        report.append("📊 전체 요약")
        report.append("-" * 30)
        report.append(f"총 연산 수: {summary['total_operations']}")
        report.append(f"처리된 문서 수: {summary['total_documents_processed']:,}")
        report.append(f"총 에러 수: {summary['total_errors']}")
        report.append(f"평균 응답시간: {summary['avg_response_time']:.2f}ms")
        report.append(f"가장 느린 연산: {summary['slowest_operation']}")
        report.append(f"가장 빠른 연산: {summary['fastest_operation']}")
        report.append("")
        
        # 연산별 상세 분석
        report.append("🔍 연산별 성능 분석")
        report.append("-" * 30)
        
        for operation, data in analysis['operations'].items():
            report.append(f"📋 {operation}")
            report.append(f"  평균 시간: {data['avg_time']:.2f}ms")
            report.append(f"  최대 시간: {data['max_time']:.2f}ms")
            report.append(f"  최소 시간: {data['min_time']:.2f}ms")
            report.append(f"  처리 문서: {data['documents_processed']:,}개")
            report.append(f"  처리량: {data['throughput']:.2f} docs/sec")
            if data['error_count'] > 0:
                report.append(f"  에러 수: {data['error_count']}")
            report.append("")
            
        # 성능 기준 평가
        report.append("🎯 성능 평가")
        report.append("-" * 30)
        
        performance_criteria = {
            'single_find_indexed': 5,     # 5ms 이하
            'multiple_find': 50,          # 50ms 이하
            'aggregation_pipeline': 200,  # 200ms 이하
            'document_insert': 10,        # 10ms 이하
            'document_update': 20,        # 20ms 이하
        }
        
        for operation, data in analysis['operations'].items():
            if operation in performance_criteria:
                target = performance_criteria[operation]
                status = "✅ 우수" if data['avg_time'] <= target else "⚠️ 개선필요" if data['avg_time'] <= target * 2 else "❌ 느림"
                report.append(f"  {operation}: {data['avg_time']:.2f}ms (기준: ≤{target}ms) {status}")
                
        report.append("")
        
        # 개선 권장사항
        if analysis['recommendations']:
            report.append("💡 성능 개선 권장사항")
            report.append("-" * 30)
            for i, recommendation in enumerate(analysis['recommendations'], 1):
                report.append(f"  {i}. {recommendation}")
            report.append("")
            
        return "\n".join(report)

async def main():
    """메인 함수"""
    db_test = DatabasePerformanceTest()
    
    try:
        # 데이터베이스 설정
        await db_test.setup_database()
        
        # 테스트 데이터 생성
        await db_test.create_test_data(1000)
        
        # 기본 연산 테스트
        print("🧪 기본 연산 성능 테스트 실행 중...")
        basic_results = await db_test.test_basic_operations()
        
        # 동시 연산 테스트
        print("🔄 동시 연산 성능 테스트 실행 중...")
        concurrent_results = await db_test.test_concurrent_operations(10)
        
        # 쿼리 최적화 테스트
        print("⚡ 쿼리 최적화 테스트 실행 중...")
        optimization_results = await db_test.test_query_optimization()
        
        # 전체 결과 분석
        all_results = basic_results + concurrent_results + optimization_results
        analysis = db_test.analyze_results(all_results)
        
        # 리포트 생성
        report = db_test.generate_report(analysis)
        print(report)
        
        # 결과 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 텍스트 리포트
        report_file = f"db_performance_report_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
            
        # JSON 결과
        json_file = f"db_performance_results_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            # 결과를 JSON 직렬화 가능한 형태로 변환
            json_data = {
                'analysis': analysis,
                'raw_results': [
                    {
                        'operation': r.operation,
                        'avg_time': r.avg_time,
                        'max_time': r.max_time,
                        'min_time': r.min_time,
                        'documents_processed': r.documents_processed,
                        'error_count': len(r.errors),
                        'errors': r.errors
                    }
                    for r in all_results
                ]
            }
            json.dump(json_data, f, indent=2, ensure_ascii=False)
            
        print(f"\n📄 리포트 저장: {report_file}")
        print(f"📊 JSON 결과 저장: {json_file}")
        
    finally:
        await db_test.cleanup_database()

if __name__ == "__main__":
    asyncio.run(main())