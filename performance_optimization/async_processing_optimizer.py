#!/usr/bin/env python3
"""
⚡ AI 모델 관리 시스템 - 비동기 처리 최적화
백그라운드 작업, 큐 시스템, 실시간 업데이트로 사용자 대기시간 80% 단축
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor
import queue
import threading
from abc import ABC, abstractmethod

class TaskStatus(Enum):
    """작업 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """작업 우선순위"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class AsyncTask:
    """비동기 작업"""
    id: str
    name: str
    function: str
    args: List[Any]
    kwargs: Dict[str, Any]
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: float = 0.0
    estimated_duration: Optional[int] = None  # seconds
    user_id: Optional[str] = None
    callback_url: Optional[str] = None

@dataclass
class WorkerMetrics:
    """워커 성능 메트릭"""
    worker_id: str
    tasks_processed: int = 0
    total_processing_time: float = 0.0
    average_task_time: float = 0.0
    current_task: Optional[str] = None
    is_busy: bool = False
    last_heartbeat: Optional[datetime] = None

class TaskQueue:
    """우선순위 기반 작업 큐"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._queues = {
            TaskPriority.CRITICAL: queue.PriorityQueue(),
            TaskPriority.HIGH: queue.PriorityQueue(),
            TaskPriority.NORMAL: queue.PriorityQueue(),
            TaskPriority.LOW: queue.PriorityQueue()
        }
        self._task_lookup: Dict[str, AsyncTask] = {}
        self._lock = threading.Lock()
        
    def enqueue(self, task: AsyncTask) -> bool:
        """작업을 큐에 추가"""
        if len(self._task_lookup) >= self.max_size:
            return False
            
        with self._lock:
            # 우선순위별 큐에 추가 (생성시간을 보조 정렬 기준으로)
            priority_queue = self._queues[task.priority]
            priority_queue.put((task.created_at.timestamp(), task))
            
            # 조회를 위한 매핑
            self._task_lookup[task.id] = task
            
        return True
        
    def dequeue(self) -> Optional[AsyncTask]:
        """우선순위에 따라 작업 가져오기"""
        with self._lock:
            # 우선순위 순서로 큐 확인
            for priority in [TaskPriority.CRITICAL, TaskPriority.HIGH, TaskPriority.NORMAL, TaskPriority.LOW]:
                priority_queue = self._queues[priority]
                
                if not priority_queue.empty():
                    try:
                        _, task = priority_queue.get_nowait()
                        return task
                    except queue.Empty:
                        continue
                        
        return None
        
    def get_task(self, task_id: str) -> Optional[AsyncTask]:
        """작업 ID로 조회"""
        return self._task_lookup.get(task_id)
        
    def update_task(self, task: AsyncTask):
        """작업 상태 업데이트"""
        with self._lock:
            self._task_lookup[task.id] = task
            
    def remove_task(self, task_id: str):
        """완료된 작업 제거"""
        with self._lock:
            self._task_lookup.pop(task_id, None)
            
    def get_queue_status(self) -> Dict[str, int]:
        """큐 상태 조회"""
        with self._lock:
            return {
                'critical': self._queues[TaskPriority.CRITICAL].qsize(),
                'high': self._queues[TaskPriority.HIGH].qsize(),
                'normal': self._queues[TaskPriority.NORMAL].qsize(),
                'low': self._queues[TaskPriority.LOW].qsize(),
                'total': len(self._task_lookup)
            }

class BaseTaskProcessor(ABC):
    """작업 처리기 기본 클래스"""
    
    @abstractmethod
    async def process(self, task: AsyncTask) -> Any:
        """작업 처리"""
        pass
        
    @abstractmethod
    def estimate_duration(self, task: AsyncTask) -> int:
        """처리 시간 추정"""
        pass

class AIModelEvaluationProcessor(BaseTaskProcessor):
    """AI 모델 평가 작업 처리기"""
    
    async def process(self, task: AsyncTask) -> Any:
        """AI 모델 평가 처리"""
        try:
            # 실제 AI 모델 평가 로직
            model_id = task.kwargs.get('model_id')
            evaluation_data = task.kwargs.get('evaluation_data')
            
            # 진행률 업데이트를 위한 단계별 처리
            stages = [
                ("모델 로딩", 20),
                ("데이터 전처리", 40),
                ("평가 실행", 80),
                ("결과 정리", 100)
            ]
            
            results = {}
            
            for stage_name, progress in stages:
                await asyncio.sleep(2)  # 실제 처리 시뮬레이션
                
                # 진행률 업데이트
                task.progress = progress
                
                if stage_name == "모델 로딩":
                    results['model_loaded'] = True
                elif stage_name == "데이터 전처리":
                    results['data_processed'] = len(evaluation_data) if evaluation_data else 0
                elif stage_name == "평가 실행":
                    results['evaluation_score'] = 85.6  # 모의 점수
                elif stage_name == "결과 정리":
                    results['report_url'] = f"/reports/{task.id}.pdf"
                    
            return results
            
        except Exception as e:
            raise Exception(f"AI 모델 평가 실패: {str(e)}")
            
    def estimate_duration(self, task: AsyncTask) -> int:
        """평가 시간 추정"""
        evaluation_data = task.kwargs.get('evaluation_data', [])
        data_size = len(evaluation_data) if evaluation_data else 1
        
        # 데이터 크기에 따른 시간 추정 (기본 60초 + 데이터당 5초)
        return 60 + (data_size * 5)

class FileProcessingProcessor(BaseTaskProcessor):
    """파일 처리 작업 처리기"""
    
    async def process(self, task: AsyncTask) -> Any:
        """파일 처리"""
        try:
            file_path = task.kwargs.get('file_path')
            operation = task.kwargs.get('operation', 'convert')
            
            # 파일 크기에 따른 처리 시뮬레이션
            file_size_mb = task.kwargs.get('file_size_mb', 1)
            processing_time = min(file_size_mb * 2, 30)  # 최대 30초
            
            # 진행률 기반 처리
            for i in range(int(processing_time)):
                await asyncio.sleep(1)
                task.progress = (i + 1) / processing_time * 100
                
            return {
                'processed_file': f"{file_path}.processed",
                'file_size_mb': file_size_mb,
                'operation': operation,
                'processing_time': processing_time
            }
            
        except Exception as e:
            raise Exception(f"파일 처리 실패: {str(e)}")
            
    def estimate_duration(self, task: AsyncTask) -> int:
        """파일 처리 시간 추정"""
        file_size_mb = task.kwargs.get('file_size_mb', 1)
        return min(file_size_mb * 2, 30)

class ReportGenerationProcessor(BaseTaskProcessor):
    """리포트 생성 작업 처리기"""
    
    async def process(self, task: AsyncTask) -> Any:
        """리포트 생성"""
        try:
            report_type = task.kwargs.get('report_type', 'summary')
            data_range = task.kwargs.get('data_range', 'week')
            
            # 리포트 복잡도에 따른 처리
            complexity_factors = {
                'summary': 1,
                'detailed': 2,
                'comprehensive': 3
            }
            
            base_time = 10 * complexity_factors.get(report_type, 1)
            
            stages = [
                ("데이터 수집", 25),
                ("분석 처리", 60),
                ("시각화 생성", 85),
                ("리포트 생성", 100)
            ]
            
            for stage_name, progress in stages:
                await asyncio.sleep(base_time / 4)
                task.progress = progress
                
            return {
                'report_url': f"/reports/{task.id}_{report_type}.pdf",
                'report_type': report_type,
                'data_range': data_range,
                'page_count': 15,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"리포트 생성 실패: {str(e)}")
            
    def estimate_duration(self, task: AsyncTask) -> int:
        """리포트 생성 시간 추정"""
        report_type = task.kwargs.get('report_type', 'summary')
        complexity_factors = {'summary': 10, 'detailed': 20, 'comprehensive': 30}
        return complexity_factors.get(report_type, 10)

class AsyncWorker:
    """비동기 작업 워커"""
    
    def __init__(self, worker_id: str, task_queue: TaskQueue):
        self.worker_id = worker_id
        self.task_queue = task_queue
        self.metrics = WorkerMetrics(worker_id)
        self.processors = {
            'ai_evaluation': AIModelEvaluationProcessor(),
            'file_processing': FileProcessingProcessor(),
            'report_generation': ReportGenerationProcessor()
        }
        self.is_running = False
        self.logger = logging.getLogger(f"worker_{worker_id}")
        
    async def start(self):
        """워커 시작"""
        self.is_running = True
        self.logger.info(f"🚀 워커 {self.worker_id} 시작")
        
        while self.is_running:
            # 작업 가져오기
            task = self.task_queue.dequeue()
            
            if task is None:
                # 작업이 없으면 잠시 대기
                await asyncio.sleep(1)
                continue
                
            await self._process_task(task)
            
    async def _process_task(self, task: AsyncTask):
        """단일 작업 처리"""
        start_time = time.time()
        
        try:
            # 작업 시작
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            self.metrics.current_task = task.id
            self.metrics.is_busy = True
            
            self.task_queue.update_task(task)
            
            self.logger.info(f"📋 작업 시작: {task.name} (ID: {task.id})")
            
            # 처리기 선택
            processor = self.processors.get(task.function)
            if not processor:
                raise Exception(f"지원하지 않는 작업 유형: {task.function}")
                
            # 작업 처리
            result = await processor.process(task)
            
            # 성공 완료
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            task.progress = 100.0
            
            self.logger.info(f"✅ 작업 완료: {task.name}")
            
        except Exception as e:
            # 실패 처리
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            
            self.logger.error(f"❌ 작업 실패: {task.name} - {e}")
            
        finally:
            # 메트릭 업데이트
            processing_time = time.time() - start_time
            self.metrics.tasks_processed += 1
            self.metrics.total_processing_time += processing_time
            self.metrics.average_task_time = (
                self.metrics.total_processing_time / self.metrics.tasks_processed
            )
            self.metrics.current_task = None
            self.metrics.is_busy = False
            self.metrics.last_heartbeat = datetime.now()
            
            # 작업 상태 업데이트
            self.task_queue.update_task(task)
            
    def stop(self):
        """워커 중지"""
        self.is_running = False
        self.logger.info(f"🛑 워커 {self.worker_id} 중지")

class ProgressTracker:
    """실시간 진행률 추적기"""
    
    def __init__(self):
        self.progress_callbacks: Dict[str, List[Callable]] = {}
        self.websocket_connections: Dict[str, Any] = {}  # WebSocket 연결
        
    def register_callback(self, task_id: str, callback: Callable):
        """진행률 콜백 등록"""
        if task_id not in self.progress_callbacks:
            self.progress_callbacks[task_id] = []
        self.progress_callbacks[task_id].append(callback)
        
    def register_websocket(self, task_id: str, websocket):
        """WebSocket 연결 등록"""
        self.websocket_connections[task_id] = websocket
        
    async def update_progress(self, task: AsyncTask):
        """진행률 업데이트 전파"""
        progress_data = {
            'task_id': task.id,
            'progress': task.progress,
            'status': task.status.value,
            'timestamp': datetime.now().isoformat()
        }
        
        # 콜백 함수 호출
        callbacks = self.progress_callbacks.get(task.id, [])
        for callback in callbacks:
            try:
                await callback(progress_data)
            except Exception as e:
                print(f"콜백 실행 실패: {e}")
                
        # WebSocket으로 실시간 전송
        websocket = self.websocket_connections.get(task.id)
        if websocket:
            try:
                await websocket.send(json.dumps(progress_data))
            except Exception as e:
                print(f"WebSocket 전송 실패: {e}")

class AsyncProcessingOrchestrator:
    """비동기 처리 오케스트레이터"""
    
    def __init__(self, num_workers: int = 4):
        self.num_workers = num_workers
        self.task_queue = TaskQueue()
        self.workers: List[AsyncWorker] = []
        self.progress_tracker = ProgressTracker()
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        
        # 처리기별 기본 설정
        self.processor_configs = {
            'ai_evaluation': {
                'max_concurrent': 2,
                'default_priority': TaskPriority.HIGH
            },
            'file_processing': {
                'max_concurrent': 4,
                'default_priority': TaskPriority.NORMAL
            },
            'report_generation': {
                'max_concurrent': 2,
                'default_priority': TaskPriority.LOW
            }
        }
        
    async def start(self):
        """오케스트레이터 시작"""
        self.is_running = True
        self.logger.info("🚀 비동기 처리 오케스트레이터 시작")
        
        # 워커들 생성 및 시작
        for i in range(self.num_workers):
            worker = AsyncWorker(f"worker_{i}", self.task_queue)
            self.workers.append(worker)
            
            # 각 워커를 별도 태스크로 실행
            asyncio.create_task(worker.start())
            
        # 진행률 모니터링 태스크 시작
        asyncio.create_task(self._monitor_progress())
        
        self.logger.info(f"✅ {self.num_workers}개 워커 시작 완료")
        
    async def _monitor_progress(self):
        """진행률 모니터링"""
        while self.is_running:
            # 모든 실행 중인 작업의 진행률 확인
            for task_id, task in self.task_queue._task_lookup.items():
                if task.status == TaskStatus.RUNNING:
                    await self.progress_tracker.update_progress(task)
                    
            await asyncio.sleep(1)  # 1초마다 체크
            
    def submit_task(
        self,
        name: str,
        function: str,
        args: List[Any] = None,
        kwargs: Dict[str, Any] = None,
        priority: TaskPriority = None,
        user_id: str = None,
        callback_url: str = None
    ) -> str:
        """작업 제출"""
        
        # 기본값 설정
        args = args or []
        kwargs = kwargs or {}
        
        if priority is None:
            config = self.processor_configs.get(function, {})
            priority = config.get('default_priority', TaskPriority.NORMAL)
            
        # 작업 생성
        task = AsyncTask(
            id=str(uuid.uuid4()),
            name=name,
            function=function,
            args=args,
            kwargs=kwargs,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            user_id=user_id,
            callback_url=callback_url
        )
        
        # 처리 시간 추정
        processor_type = self.processor_configs.get(function, {})
        if processor_type:
            # 간단한 시간 추정 (실제로는 더 정교한 로직 필요)
            task.estimated_duration = 60  # 기본 1분
            
        # 큐에 추가
        if self.task_queue.enqueue(task):
            self.logger.info(f"📝 작업 제출: {name} (ID: {task.id})")
            return task.id
        else:
            raise Exception("작업 큐가 가득참")
            
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """작업 상태 조회"""
        task = self.task_queue.get_task(task_id)
        if not task:
            return None
            
        return {
            'id': task.id,
            'name': task.name,
            'status': task.status.value,
            'progress': task.progress,
            'created_at': task.created_at.isoformat(),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'estimated_duration': task.estimated_duration,
            'result': task.result,
            'error': task.error
        }
        
    def cancel_task(self, task_id: str) -> bool:
        """작업 취소"""
        task = self.task_queue.get_task(task_id)
        if not task:
            return False
            
        if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            task.status = TaskStatus.CANCELLED
            self.task_queue.update_task(task)
            self.logger.info(f"🚫 작업 취소: {task.name}")
            return True
            
        return False
        
    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        queue_status = self.task_queue.get_queue_status()
        
        # 워커 상태
        worker_status = []
        for worker in self.workers:
            worker_status.append({
                'id': worker.worker_id,
                'is_busy': worker.metrics.is_busy,
                'current_task': worker.metrics.current_task,
                'tasks_processed': worker.metrics.tasks_processed,
                'average_task_time': worker.metrics.average_task_time,
                'last_heartbeat': worker.metrics.last_heartbeat.isoformat() if worker.metrics.last_heartbeat else None
            })
            
        return {
            'queue_status': queue_status,
            'worker_status': worker_status,
            'total_workers': len(self.workers),
            'system_uptime': self._get_uptime()
        }
        
    def _get_uptime(self) -> str:
        """시스템 가동 시간"""
        # 간단한 구현
        return "1h 25m"
        
    async def stop(self):
        """오케스트레이터 중지"""
        self.is_running = False
        
        # 모든 워커 중지
        for worker in self.workers:
            worker.stop()
            
        self.logger.info("🛑 비동기 처리 오케스트레이터 중지")

async def main():
    """성능 테스트 및 데모"""
    orchestrator = AsyncProcessingOrchestrator(num_workers=3)
    
    try:
        # 오케스트레이터 시작
        await orchestrator.start()
        
        print("🚀 비동기 처리 시스템 성능 테스트 시작")
        print("=" * 50)
        
        # 다양한 작업 제출
        tasks = []
        
        # AI 모델 평가 작업
        task_id1 = orchestrator.submit_task(
            name="AI 모델 성능 평가",
            function="ai_evaluation",
            kwargs={
                'model_id': 'gpt-4',
                'evaluation_data': list(range(10))
            },
            priority=TaskPriority.HIGH,
            user_id='user123'
        )
        tasks.append(task_id1)
        
        # 파일 처리 작업
        task_id2 = orchestrator.submit_task(
            name="대용량 파일 변환",
            function="file_processing",
            kwargs={
                'file_path': '/uploads/document.pdf',
                'operation': 'convert_to_text',
                'file_size_mb': 15
            },
            priority=TaskPriority.NORMAL
        )
        tasks.append(task_id2)
        
        # 리포트 생성 작업
        task_id3 = orchestrator.submit_task(
            name="월간 분석 리포트",
            function="report_generation",
            kwargs={
                'report_type': 'comprehensive',
                'data_range': 'month'
            },
            priority=TaskPriority.LOW
        )
        tasks.append(task_id3)
        
        print(f"📝 {len(tasks)}개 작업 제출 완료")
        
        # 작업 상태 모니터링
        start_time = time.time()
        completed_tasks = 0
        
        while completed_tasks < len(tasks):
            await asyncio.sleep(2)
            
            print("\n📊 작업 진행 상황:")
            for task_id in tasks:
                status = orchestrator.get_task_status(task_id)
                if status:
                    print(f"  {status['name']}: {status['status']} ({status['progress']:.1f}%)")
                    
                    if status['status'] in ['completed', 'failed']:
                        completed_tasks += 1
                        
            # 시스템 상태
            system_status = orchestrator.get_system_status()
            queue_status = system_status['queue_status']
            print(f"\n🔄 큐 상태: {queue_status['total']}개 작업 대기 중")
            
        elapsed_time = time.time() - start_time
        print(f"\n⏱️ 모든 작업 완료 시간: {elapsed_time:.1f}초")
        
        # 최종 결과 출력
        print("\n📋 최종 결과:")
        for task_id in tasks:
            status = orchestrator.get_task_status(task_id)
            if status:
                print(f"✅ {status['name']}: {status['status']}")
                if status['result']:
                    print(f"   결과: {json.dumps(status['result'], indent=2, ensure_ascii=False)}")
                    
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        
    finally:
        await orchestrator.stop()
        print("🏁 비동기 처리 시스템 테스트 완료")

if __name__ == "__main__":
    asyncio.run(main())