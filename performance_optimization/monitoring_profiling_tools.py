#!/usr/bin/env python3
"""
📊 AI 모델 관리 시스템 - 모니터링 및 프로파일링 도구
실시간 성능 모니터링, APM, 자동 알림 시스템
"""

import asyncio
import time
import json
import psutil
import logging
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import statistics
from collections import deque, defaultdict
import subprocess
import os
import socket

class MetricType(Enum):
    """메트릭 유형"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class AlertLevel(Enum):
    """알림 레벨"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Metric:
    """메트릭 데이터"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    metric_type: MetricType

@dataclass
class Alert:
    """알림 데이터"""
    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    metric_name: str
    current_value: float
    threshold_value: float
    resolved: bool = False

@dataclass
class SystemHealth:
    """시스템 건강 상태"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    process_count: int
    uptime_seconds: float
    load_average: List[float]

class MetricsCollector:
    """메트릭 수집기"""
    
    def __init__(self, collection_interval: int = 10):
        self.collection_interval = collection_interval
        self.metrics: deque = deque(maxlen=1000)  # 최근 1000개 메트릭
        self.custom_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.is_collecting = False
        self.logger = logging.getLogger(__name__)
        
        # 시스템 기준 메트릭
        self.baseline_metrics = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'response_time': 0.0,
            'throughput': 0.0
        }
        
    def start_collection(self):
        """메트릭 수집 시작"""
        self.is_collecting = True
        self.logger.info("📊 메트릭 수집 시작")
        
        # 별도 스레드에서 수집
        collection_thread = threading.Thread(target=self._collect_system_metrics)
        collection_thread.daemon = True
        collection_thread.start()
        
    def stop_collection(self):
        """메트릭 수집 중지"""
        self.is_collecting = False
        self.logger.info("🛑 메트릭 수집 중지")
        
    def _collect_system_metrics(self):
        """시스템 메트릭 수집"""
        while self.is_collecting:
            try:
                timestamp = datetime.now()
                
                # CPU 사용률
                cpu_usage = psutil.cpu_percent(interval=1)
                self._add_metric("system.cpu.usage", cpu_usage, timestamp, {"unit": "percent"})
                
                # 메모리 사용률
                memory = psutil.virtual_memory()
                self._add_metric("system.memory.usage", memory.percent, timestamp, {"unit": "percent"})
                self._add_metric("system.memory.available", memory.available / (1024**3), timestamp, {"unit": "GB"})
                
                # 디스크 사용률
                disk = psutil.disk_usage('/')
                disk_usage = (disk.used / disk.total) * 100
                self._add_metric("system.disk.usage", disk_usage, timestamp, {"unit": "percent"})
                
                # 네트워크 I/O
                network = psutil.net_io_counters()
                self._add_metric("system.network.bytes_sent", network.bytes_sent, timestamp, {"unit": "bytes"})
                self._add_metric("system.network.bytes_recv", network.bytes_recv, timestamp, {"unit": "bytes"})
                
                # 프로세스 수
                process_count = len(psutil.pids())
                self._add_metric("system.process.count", process_count, timestamp, {"unit": "count"})
                
                # 로드 평균 (Unix 시스템)
                if hasattr(os, 'getloadavg'):
                    load_avg = os.getloadavg()
                    self._add_metric("system.load.1min", load_avg[0], timestamp, {"unit": "load"})
                    self._add_metric("system.load.5min", load_avg[1], timestamp, {"unit": "load"})
                    self._add_metric("system.load.15min", load_avg[2], timestamp, {"unit": "load"})
                
            except Exception as e:
                self.logger.error(f"시스템 메트릭 수집 실패: {e}")
                
            time.sleep(self.collection_interval)
            
    def _add_metric(self, name: str, value: float, timestamp: datetime, tags: Dict[str, str]):
        """메트릭 추가"""
        metric = Metric(
            name=name,
            value=value,
            timestamp=timestamp,
            tags=tags,
            metric_type=MetricType.GAUGE
        )
        self.metrics.append(metric)
        
    def record_custom_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """커스텀 메트릭 기록"""
        tags = tags or {}
        timestamp = datetime.now()
        
        metric = Metric(
            name=name,
            value=value,
            timestamp=timestamp,
            tags=tags,
            metric_type=MetricType.GAUGE
        )
        
        self.custom_metrics[name].append(metric)
        
    def get_latest_metrics(self, metric_name: str = None, limit: int = 10) -> List[Metric]:
        """최신 메트릭 조회"""
        if metric_name:
            return list(self.custom_metrics.get(metric_name, deque()))[-limit:]
        else:
            return list(self.metrics)[-limit:]
            
    def get_metric_summary(self, metric_name: str, duration_minutes: int = 60) -> Dict[str, float]:
        """메트릭 요약 통계"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        # 해당 메트릭 필터링
        filtered_metrics = [
            m for m in self.metrics 
            if m.name == metric_name and m.timestamp >= cutoff_time
        ]
        
        if not filtered_metrics:
            return {}
            
        values = [m.value for m in filtered_metrics]
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
            'latest': values[-1] if values else 0
        }

class ApplicationProfiler:
    """애플리케이션 프로파일러"""
    
    def __init__(self):
        self.request_times: deque = deque(maxlen=1000)
        self.endpoint_stats: Dict[str, List[float]] = defaultdict(list)
        self.database_query_times: deque = deque(maxlen=500)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.logger = logging.getLogger(__name__)
        
    def profile_request(self, endpoint: str, execution_time: float, status_code: int):
        """요청 프로파일링"""
        timestamp = datetime.now()
        
        # 전체 요청 시간 기록
        self.request_times.append({
            'endpoint': endpoint,
            'time': execution_time,
            'status_code': status_code,
            'timestamp': timestamp
        })
        
        # 엔드포인트별 통계
        self.endpoint_stats[endpoint].append(execution_time)
        
        # 에러 카운트
        if status_code >= 400:
            self.error_counts[f"{endpoint}_{status_code}"] += 1
            
    def profile_database_query(self, query_type: str, execution_time: float):
        """데이터베이스 쿼리 프로파일링"""
        self.database_query_times.append({
            'query_type': query_type,
            'time': execution_time,
            'timestamp': datetime.now()
        })
        
    def get_performance_report(self) -> Dict[str, Any]:
        """성능 리포트 생성"""
        if not self.request_times:
            return {"message": "충분한 데이터가 없습니다"}
            
        # 최근 요청들 분석
        recent_requests = list(self.request_times)[-100:]  # 최근 100개
        request_times = [r['time'] for r in recent_requests]
        
        # 응답시간 통계
        response_time_stats = {
            'avg_response_time': statistics.mean(request_times),
            'p50_response_time': statistics.median(request_times),
            'p95_response_time': sorted(request_times)[int(len(request_times) * 0.95)] if request_times else 0,
            'p99_response_time': sorted(request_times)[int(len(request_times) * 0.99)] if request_times else 0,
            'max_response_time': max(request_times),
            'min_response_time': min(request_times)
        }
        
        # 엔드포인트별 성능
        endpoint_performance = {}
        for endpoint, times in self.endpoint_stats.items():
            if times:
                endpoint_performance[endpoint] = {
                    'avg_time': statistics.mean(times[-50:]),  # 최근 50개
                    'request_count': len(times),
                    'max_time': max(times[-50:]),
                    'min_time': min(times[-50:])
                }
                
        # 에러율 계산
        total_requests = len(recent_requests)
        error_requests = len([r for r in recent_requests if r['status_code'] >= 400])
        error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0
        
        # 데이터베이스 성능
        db_performance = {}
        if self.database_query_times:
            recent_db_queries = list(self.database_query_times)[-100:]
            db_times = [q['time'] for q in recent_db_queries]
            db_performance = {
                'avg_query_time': statistics.mean(db_times),
                'query_count': len(db_times),
                'max_query_time': max(db_times),
                'slow_queries': len([t for t in db_times if t > 1.0])  # 1초 이상
            }
            
        return {
            'response_time_stats': response_time_stats,
            'endpoint_performance': endpoint_performance,
            'error_rate': error_rate,
            'database_performance': db_performance,
            'total_requests': total_requests,
            'analysis_period': f"최근 {len(recent_requests)}개 요청"
        }
        
    def get_slow_endpoints(self, threshold_seconds: float = 2.0) -> List[Dict[str, Any]]:
        """느린 엔드포인트 식별"""
        slow_endpoints = []
        
        for endpoint, times in self.endpoint_stats.items():
            if times:
                avg_time = statistics.mean(times[-20:])  # 최근 20개 평균
                if avg_time > threshold_seconds:
                    slow_endpoints.append({
                        'endpoint': endpoint,
                        'avg_response_time': avg_time,
                        'max_response_time': max(times[-20:]),
                        'request_count': len(times[-20:])
                    })
                    
        return sorted(slow_endpoints, key=lambda x: x['avg_response_time'], reverse=True)

class AlertManager:
    """알림 관리자"""
    
    def __init__(self):
        self.alert_rules: List[Dict[str, Any]] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.notification_callbacks: List[Callable] = []
        self.logger = logging.getLogger(__name__)
        
        # 기본 알림 규칙 설정
        self._setup_default_rules()
        
    def _setup_default_rules(self):
        """기본 알림 규칙 설정"""
        self.alert_rules = [
            {
                'name': 'high_cpu_usage',
                'metric': 'system.cpu.usage',
                'threshold': 80.0,
                'operator': '>',
                'level': AlertLevel.WARNING,
                'duration_minutes': 5
            },
            {
                'name': 'high_memory_usage',
                'metric': 'system.memory.usage',
                'threshold': 85.0,
                'operator': '>',
                'level': AlertLevel.WARNING,
                'duration_minutes': 3
            },
            {
                'name': 'disk_space_low',
                'metric': 'system.disk.usage',
                'threshold': 90.0,
                'operator': '>',
                'level': AlertLevel.ERROR,
                'duration_minutes': 1
            },
            {
                'name': 'high_response_time',
                'metric': 'app.response_time',
                'threshold': 5.0,
                'operator': '>',
                'level': AlertLevel.WARNING,
                'duration_minutes': 2
            },
            {
                'name': 'high_error_rate',
                'metric': 'app.error_rate',
                'threshold': 5.0,
                'operator': '>',
                'level': AlertLevel.ERROR,
                'duration_minutes': 1
            }
        ]
        
    def add_alert_rule(self, name: str, metric: str, threshold: float, 
                      operator: str, level: AlertLevel, duration_minutes: int = 5):
        """알림 규칙 추가"""
        rule = {
            'name': name,
            'metric': metric,
            'threshold': threshold,
            'operator': operator,
            'level': level,
            'duration_minutes': duration_minutes
        }
        self.alert_rules.append(rule)
        
    def check_alerts(self, metrics: List[Metric]):
        """알림 규칙 확인"""
        for rule in self.alert_rules:
            metric_name = rule['metric']
            threshold = rule['threshold']
            operator = rule['operator']
            
            # 해당 메트릭 찾기
            relevant_metrics = [m for m in metrics if m.name == metric_name]
            
            if not relevant_metrics:
                continue
                
            latest_metric = relevant_metrics[-1]
            current_value = latest_metric.value
            
            # 임계값 확인
            alert_triggered = False
            if operator == '>' and current_value > threshold:
                alert_triggered = True
            elif operator == '<' and current_value < threshold:
                alert_triggered = True
            elif operator == '=' and current_value == threshold:
                alert_triggered = True
                
            if alert_triggered:
                self._trigger_alert(rule, current_value)
            else:
                self._resolve_alert(rule['name'])
                
    def _trigger_alert(self, rule: Dict[str, Any], current_value: float):
        """알림 발생"""
        alert_id = rule['name']
        
        # 이미 활성화된 알림인지 확인
        if alert_id in self.active_alerts:
            return
            
        alert = Alert(
            id=alert_id,
            level=rule['level'],
            title=f"{rule['name'].replace('_', ' ').title()}",
            message=f"{rule['metric']} 값이 임계값을 초과했습니다. 현재: {current_value:.2f}, 임계값: {rule['threshold']:.2f}",
            timestamp=datetime.now(),
            metric_name=rule['metric'],
            current_value=current_value,
            threshold_value=rule['threshold']
        )
        
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # 알림 전송
        self._send_notification(alert)
        
        self.logger.warning(f"🚨 알림 발생: {alert.title} - {alert.message}")
        
    def _resolve_alert(self, alert_id: str):
        """알림 해결"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            del self.active_alerts[alert_id]
            
            self.logger.info(f"✅ 알림 해결: {alert.title}")
            
    def _send_notification(self, alert: Alert):
        """알림 전송"""
        for callback in self.notification_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"알림 콜백 실행 실패: {e}")
                
    def add_notification_callback(self, callback: Callable):
        """알림 콜백 추가"""
        self.notification_callbacks.append(callback)
        
    def get_active_alerts(self) -> List[Alert]:
        """활성 알림 조회"""
        return list(self.active_alerts.values())
        
    def get_alert_history(self, limit: int = 50) -> List[Alert]:
        """알림 히스토리 조회"""
        return list(self.alert_history)[-limit:]

class PerformanceMonitor:
    """통합 성능 모니터"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.profiler = ApplicationProfiler()
        self.alert_manager = AlertManager()
        self.logger = logging.getLogger(__name__)
        
        # 모니터링 설정
        self.monitoring_active = False
        self.dashboard_data = {}
        
        # 알림 콜백 설정
        self.alert_manager.add_notification_callback(self._handle_alert)
        
    def start_monitoring(self):
        """모니터링 시작"""
        self.monitoring_active = True
        self.metrics_collector.start_collection()
        
        # 알림 체크 스레드 시작
        alert_thread = threading.Thread(target=self._alert_check_loop)
        alert_thread.daemon = True
        alert_thread.start()
        
        self.logger.info("🔍 성능 모니터링 시작")
        
    def stop_monitoring(self):
        """모니터링 중지"""
        self.monitoring_active = False
        self.metrics_collector.stop_collection()
        self.logger.info("🛑 성능 모니터링 중지")
        
    def _alert_check_loop(self):
        """알림 체크 루프"""
        while self.monitoring_active:
            try:
                # 최근 메트릭으로 알림 확인
                recent_metrics = self.metrics_collector.get_latest_metrics(limit=50)
                self.alert_manager.check_alerts(recent_metrics)
                
                # 대시보드 데이터 업데이트
                self._update_dashboard_data()
                
            except Exception as e:
                self.logger.error(f"알림 체크 실패: {e}")
                
            time.sleep(30)  # 30초마다 체크
            
    def _handle_alert(self, alert: Alert):
        """알림 처리"""
        # 실제 환경에서는 이메일, 슬랙, 웹훅 등으로 전송
        print(f"🚨 알림: [{alert.level.value.upper()}] {alert.title}")
        print(f"   메시지: {alert.message}")
        print(f"   시간: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
    def _update_dashboard_data(self):
        """대시보드 데이터 업데이트"""
        # 시스템 건강 상태
        system_health = self._get_system_health()
        
        # 애플리케이션 성능
        app_performance = self.profiler.get_performance_report()
        
        # 알림 상태
        active_alerts = self.alert_manager.get_active_alerts()
        
        self.dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'system_health': asdict(system_health),
            'application_performance': app_performance,
            'active_alerts_count': len(active_alerts),
            'alert_levels': {
                'critical': len([a for a in active_alerts if a.level == AlertLevel.CRITICAL]),
                'error': len([a for a in active_alerts if a.level == AlertLevel.ERROR]),
                'warning': len([a for a in active_alerts if a.level == AlertLevel.WARNING])
            }
        }
        
    def _get_system_health(self) -> SystemHealth:
        """시스템 건강 상태 조회"""
        # CPU
        cpu_usage = psutil.cpu_percent()
        
        # 메모리
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # 디스크
        disk = psutil.disk_usage('/')
        disk_usage = (disk.used / disk.total) * 100
        
        # 네트워크
        network = psutil.net_io_counters()
        network_io = {
            'bytes_sent_mb': network.bytes_sent / (1024**2),
            'bytes_recv_mb': network.bytes_recv / (1024**2)
        }
        
        # 프로세스
        process_count = len(psutil.pids())
        
        # 업타임
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        
        # 로드 평균
        load_average = list(os.getloadavg()) if hasattr(os, 'getloadavg') else [0.0, 0.0, 0.0]
        
        return SystemHealth(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            network_io=network_io,
            process_count=process_count,
            uptime_seconds=uptime_seconds,
            load_average=load_average
        )
        
    def record_request(self, endpoint: str, execution_time: float, status_code: int = 200):
        """요청 기록"""
        self.profiler.profile_request(endpoint, execution_time, status_code)
        
        # 커스텀 메트릭 기록
        self.metrics_collector.record_custom_metric(
            "app.response_time", 
            execution_time,
            {"endpoint": endpoint, "status": str(status_code)}
        )
        
    def record_database_query(self, query_type: str, execution_time: float):
        """데이터베이스 쿼리 기록"""
        self.profiler.profile_database_query(query_type, execution_time)
        
        self.metrics_collector.record_custom_metric(
            "db.query_time",
            execution_time,
            {"query_type": query_type}
        )
        
    def get_dashboard_data(self) -> Dict[str, Any]:
        """대시보드 데이터 조회"""
        return self.dashboard_data
        
    def get_health_status(self) -> Dict[str, str]:
        """전체 건강 상태"""
        active_alerts = self.alert_manager.get_active_alerts()
        
        if any(a.level == AlertLevel.CRITICAL for a in active_alerts):
            return {"status": "critical", "message": "치명적인 문제가 감지되었습니다"}
        elif any(a.level == AlertLevel.ERROR for a in active_alerts):
            return {"status": "error", "message": "오류가 발생했습니다"}
        elif any(a.level == AlertLevel.WARNING for a in active_alerts):
            return {"status": "warning", "message": "주의가 필요합니다"}
        else:
            return {"status": "healthy", "message": "시스템이 정상 작동 중입니다"}
            
    def generate_performance_report(self) -> str:
        """성능 리포트 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 시스템 상태
        system_health = self._get_system_health()
        
        # 애플리케이션 성능
        app_performance = self.profiler.get_performance_report()
        
        # 느린 엔드포인트
        slow_endpoints = self.profiler.get_slow_endpoints()
        
        # 알림 히스토리
        alert_history = self.alert_manager.get_alert_history(limit=20)
        
        report = f"""
📊 AI 모델 관리 시스템 - 성능 모니터링 리포트
{'='*60}
생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🖥️ 시스템 상태:
- CPU 사용률: {system_health.cpu_usage:.1f}%
- 메모리 사용률: {system_health.memory_usage:.1f}%
- 디스크 사용률: {system_health.disk_usage:.1f}%
- 프로세스 수: {system_health.process_count}개
- 업타임: {system_health.uptime_seconds/3600:.1f}시간

🚀 애플리케이션 성능:
- 평균 응답시간: {app_performance.get('response_time_stats', {}).get('avg_response_time', 0):.3f}초
- P95 응답시간: {app_performance.get('response_time_stats', {}).get('p95_response_time', 0):.3f}초
- 에러율: {app_performance.get('error_rate', 0):.2f}%
- 총 요청 수: {app_performance.get('total_requests', 0)}개

🐌 느린 엔드포인트 (상위 5개):
"""
        
        for i, endpoint in enumerate(slow_endpoints[:5], 1):
            report += f"  {i}. {endpoint['endpoint']}: {endpoint['avg_response_time']:.3f}초\n"
            
        report += f"\n🚨 최근 알림 ({len(alert_history)}개):\n"
        for alert in alert_history[-10:]:
            status = "해결됨" if alert.resolved else "활성"
            report += f"  - [{alert.level.value.upper()}] {alert.title} ({status})\n"
            
        # 파일로 저장
        report_file = f"performance_monitoring_report_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
            
        self.logger.info(f"📋 성능 리포트 생성: {report_file}")
        return report

async def main():
    """모니터링 시스템 데모"""
    monitor = PerformanceMonitor()
    
    try:
        print("📊 성능 모니터링 시스템 시작")
        print("=" * 50)
        
        # 모니터링 시작
        monitor.start_monitoring()
        
        # 모의 애플리케이션 활동
        endpoints = ['/api/models', '/api/evaluations', '/api/users', '/api/reports']
        
        for i in range(20):
            # 랜덤 요청 시뮬레이션
            import random
            endpoint = random.choice(endpoints)
            response_time = random.uniform(0.1, 3.0)
            status_code = random.choice([200, 200, 200, 404, 500])  # 대부분 성공
            
            monitor.record_request(endpoint, response_time, status_code)
            
            # 데이터베이스 쿼리 시뮬레이션
            query_type = random.choice(['SELECT', 'INSERT', 'UPDATE', 'DELETE'])
            query_time = random.uniform(0.01, 1.5)
            monitor.record_database_query(query_type, query_time)
            
            await asyncio.sleep(0.5)
            
        # 잠시 대기하여 메트릭 수집
        await asyncio.sleep(10)
        
        # 대시보드 데이터 출력
        dashboard_data = monitor.get_dashboard_data()
        print("\n📊 실시간 대시보드 데이터:")
        print(json.dumps(dashboard_data, indent=2, ensure_ascii=False, default=str))
        
        # 건강 상태 확인
        health_status = monitor.get_health_status()
        print(f"\n🏥 시스템 건강 상태: {health_status['status']} - {health_status['message']}")
        
        # 성능 리포트 생성
        report = monitor.generate_performance_report()
        print("\n📋 성능 리포트가 생성되었습니다")
        
    except Exception as e:
        print(f"❌ 모니터링 실패: {e}")
        
    finally:
        monitor.stop_monitoring()
        print("🏁 성능 모니터링 시스템 종료")

if __name__ == "__main__":
    asyncio.run(main())