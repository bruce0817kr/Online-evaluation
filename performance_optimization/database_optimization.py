#!/usr/bin/env python3
"""
⚡ AI 모델 관리 시스템 - 데이터베이스 성능 최적화
MongoDB 쿼리 성능 분석 및 인덱스 최적화 자동화 도구
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import motor.motor_asyncio
import pymongo
import json
from pathlib import Path

@dataclass
class QueryPerformance:
    """쿼리 성능 메트릭"""
    query: Dict[str, Any]
    collection: str
    execution_time: float
    documents_examined: int
    documents_returned: int
    index_used: Optional[str]
    optimization_suggestions: List[str]

@dataclass
class IndexRecommendation:
    """인덱스 추천"""
    collection: str
    fields: List[str]
    index_type: str  # single, compound, text, geo
    priority: str    # high, medium, low
    estimated_improvement: float
    reasoning: str

class DatabaseOptimizer:
    """데이터베이스 성능 최적화 클래스"""
    
    def __init__(self, mongodb_url: str = "mongodb://localhost:27017/online_evaluation"):
        self.mongodb_url = mongodb_url
        self.client = None
        self.db = None
        
        # 성능 분석 결과
        self.query_performance: List[QueryPerformance] = []
        self.index_recommendations: List[IndexRecommendation] = []
        self.current_indexes: Dict[str, List[Dict]] = {}
        
        # 로깅 설정
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 최적화 설정
        self.performance_thresholds = {
            'slow_query_time': 100,      # 100ms 이상은 느린 쿼리
            'examine_ratio': 10,         # examined/returned 비율이 10:1 이상이면 비효율적
            'index_selectivity': 0.1     # 인덱스 선택도가 10% 이하면 개선 필요
        }
        
    async def connect(self):
        """데이터베이스 연결"""
        self.client = motor.motor_asyncio.AsyncIOMotorClient(self.mongodb_url)
        self.db = self.client.get_default_database()
        
        # 연결 테스트
        try:
            await self.client.admin.command('ismaster')
            self.logger.info("✅ MongoDB 연결 성공")
        except Exception as e:
            self.logger.error(f"❌ MongoDB 연결 실패: {e}")
            raise
            
    async def disconnect(self):
        """데이터베이스 연결 해제"""
        if self.client:
            self.client.close()
            
    async def analyze_all_collections(self) -> Dict[str, Any]:
        """모든 컬렉션 성능 분석"""
        self.logger.info("🔍 데이터베이스 성능 분석 시작")
        
        # 1. 현재 인덱스 정보 수집
        await self._collect_current_indexes()
        
        # 2. 실행 중인 쿼리 분석
        await self._analyze_running_queries()
        
        # 3. 느린 쿼리 로그 분석
        await self._analyze_slow_queries()
        
        # 4. 컬렉션별 통계 분석
        collection_stats = await self._analyze_collection_statistics()
        
        # 5. 인덱스 사용량 분석
        index_usage = await self._analyze_index_usage()
        
        # 6. 최적화 권장사항 생성
        await self._generate_optimization_recommendations()
        
        # 7. 종합 분석 결과
        analysis_result = {
            'timestamp': datetime.now().isoformat(),
            'collection_statistics': collection_stats,
            'index_usage': index_usage,
            'query_performance': [self._serialize_query_performance(qp) for qp in self.query_performance],
            'index_recommendations': [self._serialize_index_recommendation(ir) for ir in self.index_recommendations],
            'current_indexes': self.current_indexes,
            'optimization_summary': self._generate_optimization_summary()
        }
        
        self.logger.info("✅ 데이터베이스 성능 분석 완료")
        return analysis_result
        
    async def _collect_current_indexes(self):
        """현재 인덱스 정보 수집"""
        self.logger.info("📊 현재 인덱스 정보 수집 중...")
        
        collections = await self.db.list_collection_names()
        
        for collection_name in collections:
            collection = self.db[collection_name]
            indexes = await collection.list_indexes().to_list(length=None)
            
            self.current_indexes[collection_name] = []
            for index in indexes:
                index_info = {
                    'name': index['name'],
                    'key': index['key'],
                    'unique': index.get('unique', False),
                    'sparse': index.get('sparse', False),
                    'background': index.get('background', False),
                    'size': 0  # 크기는 별도로 계산
                }
                self.current_indexes[collection_name].append(index_info)
                
        self.logger.info(f"✅ {len(collections)}개 컬렉션의 인덱스 정보 수집 완료")
        
    async def _analyze_running_queries(self):
        """실행 중인 쿼리 분석"""
        self.logger.info("🔄 실행 중인 쿼리 분석 중...")
        
        try:
            # 현재 실행 중인 작업 조회
            current_ops = await self.db.admin.command("currentOp", {"active": True})
            
            for op in current_ops.get('inprog', []):
                if op.get('op') in ['query', 'getmore']:
                    command = op.get('command', {})
                    if 'find' in command:
                        collection_name = command['find']
                        query = command.get('filter', {})
                        duration = op.get('microsecs_running', 0) / 1000  # ms로 변환
                        
                        if duration > self.performance_thresholds['slow_query_time']:
                            # 느린 쿼리 발견
                            performance = QueryPerformance(
                                query=query,
                                collection=collection_name,
                                execution_time=duration,
                                documents_examined=0,  # currentOp에서는 정확한 값 없음
                                documents_returned=0,
                                index_used=None,
                                optimization_suggestions=["현재 실행 중인 느린 쿼리입니다"]
                            )
                            self.query_performance.append(performance)
                            
        except Exception as e:
            self.logger.warning(f"실행 중인 쿼리 분석 중 오류: {e}")
            
    async def _analyze_slow_queries(self):
        """느린 쿼리 로그 분석"""
        self.logger.info("🐌 느린 쿼리 분석 중...")
        
        # MongoDB 프로파일러 활성화 (레벨 2: 모든 작업 기록)
        try:
            # 프로파일링 설정 확인
            profile_status = await self.db.command("profile", -1)
            
            if profile_status.get('was', 0) == 0:
                # 프로파일링이 비활성화되어 있으면 임시로 활성화
                await self.db.command("profile", 2, {"slowms": 50})
                self.logger.info("📊 MongoDB 프로파일러 활성화")
                
                # 잠시 대기 (실제 쿼리 수집을 위해)
                await asyncio.sleep(2)
                
        except Exception as e:
            self.logger.warning(f"프로파일러 설정 중 오류: {e}")
            
        # 프로파일 컬렉션에서 느린 쿼리 분석
        try:
            profile_collection = self.db['system.profile']
            
            # 최근 1시간의 프로파일 데이터 조회
            one_hour_ago = datetime.now() - timedelta(hours=1)
            
            cursor = profile_collection.find({
                'ts': {'$gte': one_hour_ago},
                'op': {'$in': ['query', 'getmore']},
                'millis': {'$gte': self.performance_thresholds['slow_query_time']}
            }).sort('millis', -1).limit(100)
            
            async for profile in cursor:
                collection_name = profile.get('ns', '').split('.')[-1]
                if not collection_name or collection_name.startswith('system.'):
                    continue
                    
                query = profile.get('command', {}).get('filter', {})
                execution_time = profile.get('millis', 0)
                docs_examined = profile.get('docsExamined', 0)
                docs_returned = profile.get('docsReturned', 0)
                
                # 인덱스 사용 정보
                execution_stats = profile.get('execStats', {})
                index_used = self._extract_index_used(execution_stats)
                
                # 최적화 제안 생성
                suggestions = self._generate_query_suggestions(
                    query, docs_examined, docs_returned, index_used
                )
                
                performance = QueryPerformance(
                    query=query,
                    collection=collection_name,
                    execution_time=execution_time,
                    documents_examined=docs_examined,
                    documents_returned=docs_returned,
                    index_used=index_used,
                    optimization_suggestions=suggestions
                )
                
                self.query_performance.append(performance)
                
            self.logger.info(f"✅ {len(self.query_performance)}개의 느린 쿼리 분석 완료")
            
        except Exception as e:
            self.logger.warning(f"느린 쿼리 분석 중 오류: {e}")
            
    async def _analyze_collection_statistics(self) -> Dict[str, Any]:
        """컬렉션 통계 분석"""
        self.logger.info("📈 컬렉션 통계 분석 중...")
        
        stats = {}
        collections = await self.db.list_collection_names()
        
        for collection_name in collections:
            if collection_name.startswith('system.'):
                continue
                
            try:
                collection = self.db[collection_name]
                
                # 컬렉션 통계
                collection_stats = await self.db.command("collStats", collection_name)
                
                # 문서 수 및 크기
                document_count = collection_stats.get('count', 0)
                avg_obj_size = collection_stats.get('avgObjSize', 0)
                total_size = collection_stats.get('size', 0)
                
                # 인덱스 통계
                index_count = len(self.current_indexes.get(collection_name, []))
                total_index_size = collection_stats.get('totalIndexSize', 0)
                
                stats[collection_name] = {
                    'document_count': document_count,
                    'average_document_size': avg_obj_size,
                    'total_size_bytes': total_size,
                    'total_size_mb': round(total_size / (1024 * 1024), 2),
                    'index_count': index_count,
                    'total_index_size_bytes': total_index_size,
                    'total_index_size_mb': round(total_index_size / (1024 * 1024), 2),
                    'index_to_data_ratio': round(total_index_size / total_size * 100, 2) if total_size > 0 else 0
                }
                
            except Exception as e:
                self.logger.warning(f"컬렉션 {collection_name} 통계 수집 중 오류: {e}")
                
        return stats
        
    async def _analyze_index_usage(self) -> Dict[str, Any]:
        """인덱스 사용량 분석"""
        self.logger.info("📊 인덱스 사용량 분석 중...")
        
        usage_stats = {}
        
        for collection_name, indexes in self.current_indexes.items():
            collection = self.db[collection_name]
            
            try:
                # $indexStats 집계를 사용하여 인덱스 사용량 조회
                pipeline = [{"$indexStats": {}}]
                cursor = collection.aggregate(pipeline)
                
                collection_usage = []
                async for index_stat in cursor:
                    index_info = {
                        'name': index_stat['name'],
                        'accesses': index_stat['accesses'],
                        'since': index_stat['accesses']['since'].isoformat() if 'since' in index_stat['accesses'] else None
                    }
                    collection_usage.append(index_info)
                    
                usage_stats[collection_name] = collection_usage
                
            except Exception as e:
                self.logger.warning(f"컬렉션 {collection_name} 인덱스 사용량 분석 중 오류: {e}")
                usage_stats[collection_name] = []
                
        return usage_stats
        
    async def _generate_optimization_recommendations(self):
        """최적화 권장사항 생성"""
        self.logger.info("💡 최적화 권장사항 생성 중...")
        
        # 1. 자주 사용되는 쿼리 패턴 분석
        query_patterns = self._analyze_query_patterns()
        
        # 2. 인덱스가 없는 쿼리 필드 식별
        missing_indexes = self._identify_missing_indexes(query_patterns)
        
        # 3. 사용되지 않는 인덱스 식별
        unused_indexes = await self._identify_unused_indexes()
        
        # 4. 복합 인덱스 기회 식별
        compound_index_opportunities = self._identify_compound_index_opportunities(query_patterns)
        
        # 권장사항 생성
        for collection, fields in missing_indexes.items():
            for field_set in fields:
                if len(field_set) == 1:
                    # 단일 필드 인덱스
                    recommendation = IndexRecommendation(
                        collection=collection,
                        fields=list(field_set),
                        index_type="single",
                        priority="high",
                        estimated_improvement=self._estimate_improvement(collection, field_set),
                        reasoning=f"필드 '{field_set}'에 대한 쿼리가 빈번하지만 인덱스가 없습니다"
                    )
                else:
                    # 복합 인덱스
                    recommendation = IndexRecommendation(
                        collection=collection,
                        fields=list(field_set),
                        index_type="compound",
                        priority="medium",
                        estimated_improvement=self._estimate_improvement(collection, field_set),
                        reasoning=f"복합 쿼리 패턴 최적화를 위한 복합 인덱스 권장"
                    )
                    
                self.index_recommendations.append(recommendation)
                
        # 사용되지 않는 인덱스 제거 권장
        for collection, index_names in unused_indexes.items():
            for index_name in index_names:
                if index_name != '_id_':  # 기본 인덱스는 제외
                    recommendation = IndexRecommendation(
                        collection=collection,
                        fields=[index_name],
                        index_type="remove",
                        priority="low",
                        estimated_improvement=5.0,  # 스토리지 절약
                        reasoning=f"사용되지 않는 인덱스 '{index_name}' 제거 권장"
                    )
                    self.index_recommendations.append(recommendation)
                    
    def _analyze_query_patterns(self) -> Dict[str, List[set]]:
        """쿼리 패턴 분석"""
        patterns = {}
        
        for qp in self.query_performance:
            collection = qp.collection
            if collection not in patterns:
                patterns[collection] = []
                
            # 쿼리에서 사용된 필드 추출
            query_fields = self._extract_query_fields(qp.query)
            if query_fields:
                patterns[collection].append(set(query_fields))
                
        return patterns
        
    def _extract_query_fields(self, query: Dict[str, Any]) -> List[str]:
        """쿼리에서 필드명 추출"""
        fields = []
        
        def extract_fields_recursive(obj, prefix=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key.startswith('$'):
                        # MongoDB 연산자는 스킵
                        if isinstance(value, dict):
                            extract_fields_recursive(value, prefix)
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict):
                                    extract_fields_recursive(item, prefix)
                    else:
                        field_name = f"{prefix}.{key}" if prefix else key
                        fields.append(field_name)
                        
                        if isinstance(value, dict):
                            extract_fields_recursive(value, field_name)
                            
        extract_fields_recursive(query)
        return fields
        
    def _identify_missing_indexes(self, query_patterns: Dict[str, List[set]]) -> Dict[str, List[set]]:
        """누락된 인덱스 식별"""
        missing = {}
        
        for collection, patterns in query_patterns.items():
            existing_indexes = self.current_indexes.get(collection, [])
            existing_fields = set()
            
            for index in existing_indexes:
                for field in index['key'].keys():
                    existing_fields.add(field)
                    
            missing_patterns = []
            for pattern in patterns:
                if not any(field in existing_fields for field in pattern):
                    missing_patterns.append(pattern)
                    
            if missing_patterns:
                missing[collection] = missing_patterns
                
        return missing
        
    async def _identify_unused_indexes(self) -> Dict[str, List[str]]:
        """사용되지 않는 인덱스 식별"""
        unused = {}
        
        # 인덱스 사용량 데이터 기반으로 판단
        # 실제 구현에서는 $indexStats 결과를 사용
        
        return unused
        
    def _identify_compound_index_opportunities(self, query_patterns: Dict[str, List[set]]) -> Dict[str, List[List[str]]]:
        """복합 인덱스 기회 식별"""
        opportunities = {}
        
        for collection, patterns in query_patterns.items():
            # 자주 함께 사용되는 필드 조합 찾기
            field_combinations = {}
            
            for pattern in patterns:
                if len(pattern) > 1:
                    sorted_fields = tuple(sorted(pattern))
                    field_combinations[sorted_fields] = field_combinations.get(sorted_fields, 0) + 1
                    
            # 빈도가 높은 조합 선별
            frequent_combinations = [
                list(combo) for combo, count in field_combinations.items() 
                if count >= 3  # 3회 이상 나타나는 조합
            ]
            
            if frequent_combinations:
                opportunities[collection] = frequent_combinations
                
        return opportunities
        
    def _estimate_improvement(self, collection: str, fields: set) -> float:
        """성능 개선 예상치 계산"""
        # 간단한 휴리스틱 기반 추정
        base_improvement = 50.0  # 기본 50% 개선
        
        # 필드 수에 따른 조정
        if len(fields) > 1:
            base_improvement *= 0.8  # 복합 인덱스는 약간 낮게
            
        # 컬렉션 크기에 따른 조정
        # (실제로는 컬렉션 통계를 사용)
        
        return min(base_improvement, 90.0)  # 최대 90% 개선
        
    def _extract_index_used(self, execution_stats: Dict) -> Optional[str]:
        """실행 통계에서 사용된 인덱스 추출"""
        if 'indexName' in execution_stats:
            return execution_stats['indexName']
        return None
        
    def _generate_query_suggestions(self, query: Dict, examined: int, returned: int, index_used: Optional[str]) -> List[str]:
        """쿼리별 최적화 제안 생성"""
        suggestions = []
        
        # 검사 비율 확인
        if returned > 0 and examined / returned > self.performance_thresholds['examine_ratio']:
            suggestions.append(f"비효율적인 쿼리: {examined}개 문서 검사 후 {returned}개 반환. 인덱스 최적화 필요")
            
        # 인덱스 사용 여부
        if not index_used or index_used == "COLLSCAN":
            suggestions.append("인덱스가 사용되지 않음. 적절한 인덱스 생성 권장")
            
        # 쿼리 패턴별 제안
        if '$regex' in str(query):
            suggestions.append("정규식 쿼리는 성능에 영향을 줄 수 있음. 텍스트 인덱스 고려")
            
        if '$where' in str(query):
            suggestions.append("$where 연산자는 매우 느림. 다른 쿼리 연산자 사용 권장")
            
        return suggestions
        
    def _generate_optimization_summary(self) -> Dict[str, Any]:
        """최적화 요약 생성"""
        total_slow_queries = len(self.query_performance)
        total_recommendations = len(self.index_recommendations)
        
        high_priority_recs = len([r for r in self.index_recommendations if r.priority == "high"])
        
        estimated_total_improvement = sum([
            r.estimated_improvement for r in self.index_recommendations 
            if r.index_type != "remove"
        ])
        
        return {
            'total_slow_queries': total_slow_queries,
            'total_recommendations': total_recommendations,
            'high_priority_recommendations': high_priority_recs,
            'estimated_average_improvement': round(estimated_total_improvement / max(total_recommendations, 1), 2),
            'quick_wins': [
                r for r in self.index_recommendations 
                if r.priority == "high" and r.estimated_improvement > 50
            ][:3]  # 상위 3개 빠른 개선사항
        }
        
    def _serialize_query_performance(self, qp: QueryPerformance) -> Dict[str, Any]:
        """QueryPerformance 객체를 딕셔너리로 변환"""
        return {
            'query': qp.query,
            'collection': qp.collection,
            'execution_time': qp.execution_time,
            'documents_examined': qp.documents_examined,
            'documents_returned': qp.documents_returned,
            'index_used': qp.index_used,
            'optimization_suggestions': qp.optimization_suggestions
        }
        
    def _serialize_index_recommendation(self, ir: IndexRecommendation) -> Dict[str, Any]:
        """IndexRecommendation 객체를 딕셔너리로 변환"""
        return {
            'collection': ir.collection,
            'fields': ir.fields,
            'index_type': ir.index_type,
            'priority': ir.priority,
            'estimated_improvement': ir.estimated_improvement,
            'reasoning': ir.reasoning
        }
        
    async def apply_recommendations(self, auto_apply: bool = False) -> Dict[str, Any]:
        """권장사항 적용"""
        self.logger.info("🔧 최적화 권장사항 적용 중...")
        
        applied_changes = []
        failed_changes = []
        
        for recommendation in self.index_recommendations:
            if recommendation.index_type == "remove":
                # 인덱스 제거
                if auto_apply or recommendation.priority == "low":
                    try:
                        collection = self.db[recommendation.collection]
                        await collection.drop_index(recommendation.fields[0])
                        applied_changes.append(f"인덱스 제거: {recommendation.collection}.{recommendation.fields[0]}")
                    except Exception as e:
                        failed_changes.append(f"인덱스 제거 실패: {recommendation.collection}.{recommendation.fields[0]} - {e}")
                        
            elif recommendation.priority == "high" and (auto_apply or recommendation.estimated_improvement > 70):
                # 고우선순위 인덱스 생성
                try:
                    collection = self.db[recommendation.collection]
                    
                    if recommendation.index_type == "single":
                        index_spec = {recommendation.fields[0]: 1}
                    elif recommendation.index_type == "compound":
                        index_spec = {field: 1 for field in recommendation.fields}
                    else:
                        continue
                        
                    await collection.create_index(
                        list(index_spec.items()),
                        background=True,
                        name=f"{'_'.join(recommendation.fields)}_auto_optimized"
                    )
                    applied_changes.append(f"인덱스 생성: {recommendation.collection}.{recommendation.fields}")
                    
                except Exception as e:
                    failed_changes.append(f"인덱스 생성 실패: {recommendation.collection}.{recommendation.fields} - {e}")
                    
        result = {
            'applied_changes': applied_changes,
            'failed_changes': failed_changes,
            'total_applied': len(applied_changes),
            'total_failed': len(failed_changes)
        }
        
        self.logger.info(f"✅ {len(applied_changes)}개 변경사항 적용, {len(failed_changes)}개 실패")
        return result
        
    async def generate_optimization_report(self, analysis_result: Dict[str, Any]) -> str:
        """최적화 리포트 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"database_optimization_report_{timestamp}.json"
        
        # JSON 리포트 저장
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False, default=str)
            
        # 텍스트 요약 생성
        summary = analysis_result['optimization_summary']
        
        report_text = f"""
📊 데이터베이스 성능 최적화 리포트
{'='*50}
분석 시간: {analysis_result['timestamp']}

🔍 분석 결과:
- 느린 쿼리 발견: {summary['total_slow_queries']}개
- 최적화 권장사항: {summary['total_recommendations']}개
- 고우선순위 권장사항: {summary['high_priority_recommendations']}개
- 예상 평균 성능 개선: {summary['estimated_average_improvement']}%

💡 빠른 개선사항 (Top 3):
"""
        
        for i, quick_win in enumerate(summary.get('quick_wins', []), 1):
            if isinstance(quick_win, dict):
                report_text += f"  {i}. {quick_win.get('collection', '')}.{quick_win.get('fields', [])} "
                report_text += f"({quick_win.get('estimated_improvement', 0):.1f}% 개선 예상)\n"
                
        report_text += f"\n📄 상세 리포트: {report_file}\n"
        
        self.logger.info(f"📊 최적화 리포트 생성: {report_file}")
        return report_text

async def main():
    """메인 함수"""
    optimizer = DatabaseOptimizer()
    
    try:
        # 데이터베이스 연결
        await optimizer.connect()
        
        # 성능 분석 실행
        print("⚡ 데이터베이스 성능 최적화 시작...")
        analysis_result = await optimizer.analyze_all_collections()
        
        # 리포트 생성
        report_summary = await optimizer.generate_optimization_report(analysis_result)
        print(report_summary)
        
        # 권장사항 적용 (선택적)
        apply_changes = input("\n🔧 고우선순위 권장사항을 자동 적용하시겠습니까? (y/N): ")
        if apply_changes.lower() == 'y':
            changes_result = await optimizer.apply_recommendations(auto_apply=True)
            print(f"✅ {changes_result['total_applied']}개 변경사항이 적용되었습니다.")
            if changes_result['failed_changes']:
                print(f"❌ {changes_result['total_failed']}개 변경사항이 실패했습니다.")
                
    except Exception as e:
        print(f"❌ 최적화 과정에서 오류 발생: {e}")
        return 1
        
    finally:
        await optimizer.disconnect()
        
    print("🎯 데이터베이스 최적화 완료!")
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))