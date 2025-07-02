"""
Database Optimization and Monitoring System
Provides connection pooling, query optimization, health monitoring, and backup utilities
"""

import os
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
import motor.motor_asyncio
from motor.core import AgnosticCollection, AgnosticDatabase
from pymongo import monitoring, IndexModel
from pymongo.errors import PyMongoError
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class QueryMetrics:
    """Query performance metrics"""
    operation: str
    collection: str
    duration_ms: float
    timestamp: datetime
    command: Dict[str, Any]
    success: bool
    error: Optional[str] = None

@dataclass
class ConnectionMetrics:
    """Database connection metrics"""
    active_connections: int
    available_connections: int
    total_connections: int
    pool_utilization: float
    failed_connections: int
    average_checkout_time_ms: float

@dataclass
class DatabaseHealth:
    """Database health status"""
    is_healthy: bool
    response_time_ms: float
    connections: ConnectionMetrics
    recent_errors: List[str]
    performance_metrics: Dict[str, Any]
    timestamp: datetime

class CommandMonitor(monitoring.CommandListener):
    """MongoDB command monitoring for performance tracking"""
    
    def __init__(self, metrics_collector):
        self.metrics_collector = metrics_collector
        self.pending_commands = {}
    
    def started(self, event):
        """Track command start"""
        self.pending_commands[event.request_id] = {
            'start_time': time.time(),
            'command': event.command,
            'operation': event.command_name,
            'collection': event.command.get(event.command_name, 'unknown')
        }
    
    def succeeded(self, event):
        """Track successful command completion"""
        if event.request_id in self.pending_commands:
            command_data = self.pending_commands.pop(event.request_id)
            duration_ms = (time.time() - command_data['start_time']) * 1000
            
            metrics = QueryMetrics(
                operation=command_data['operation'],
                collection=str(command_data['collection']),
                duration_ms=duration_ms,
                timestamp=datetime.utcnow(),
                command=command_data['command'],
                success=True
            )
            
            self.metrics_collector.add_query_metric(metrics)
    
    def failed(self, event):
        """Track failed command"""
        if event.request_id in self.pending_commands:
            command_data = self.pending_commands.pop(event.request_id)
            duration_ms = (time.time() - command_data['start_time']) * 1000
            
            metrics = QueryMetrics(
                operation=command_data['operation'],
                collection=str(command_data['collection']),
                duration_ms=duration_ms,
                timestamp=datetime.utcnow(),
                command=command_data['command'],
                success=False,
                error=event.failure.get('errmsg', 'Unknown error')
            )
            
            self.metrics_collector.add_query_metric(metrics)

class ServerMonitor(monitoring.ServerListener):
    """MongoDB server monitoring for connection tracking"""
    
    def __init__(self, metrics_collector):
        self.metrics_collector = metrics_collector
    
    def opened(self, event):
        """Track server connection opened"""
        logger.debug(f"Connection opened to {event.server_address}")
        self.metrics_collector.increment_connections()
    
    def closed(self, event):
        """Track server connection closed"""
        logger.debug(f"Connection closed to {event.server_address}")
        self.metrics_collector.decrement_connections()

class DatabaseMetricsCollector:
    """Collects and manages database performance metrics"""
    
    def __init__(self, max_metrics: int = 10000):
        self.query_metrics: List[QueryMetrics] = []
        self.max_metrics = max_metrics
        self.connection_count = 0
        self.failed_connections = 0
        self.checkout_times = []
        self._lock = threading.Lock()
    
    def add_query_metric(self, metric: QueryMetrics):
        """Add query performance metric"""
        with self._lock:
            self.query_metrics.append(metric)
            
            # Keep only recent metrics
            if len(self.query_metrics) > self.max_metrics:
                self.query_metrics = self.query_metrics[-self.max_metrics:]
            
            # Log slow queries
            if metric.duration_ms > 1000:  # 1 second threshold
                logger.warning(
                    f"Slow query detected: {metric.operation} on {metric.collection} "
                    f"took {metric.duration_ms:.2f}ms"
                )
    
    def increment_connections(self):
        """Increment active connection count"""
        with self._lock:
            self.connection_count += 1
    
    def decrement_connections(self):
        """Decrement active connection count"""
        with self._lock:
            self.connection_count = max(0, self.connection_count - 1)
    
    def add_checkout_time(self, time_ms: float):
        """Add connection checkout time"""
        with self._lock:
            self.checkout_times.append(time_ms)
            
            # Keep only recent checkout times
            if len(self.checkout_times) > 1000:
                self.checkout_times = self.checkout_times[-1000:]
    
    def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get performance summary for the specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        with self._lock:
            recent_metrics = [
                m for m in self.query_metrics 
                if m.timestamp >= cutoff_time
            ]
            
            if not recent_metrics:
                return {
                    "total_queries": 0,
                    "average_duration_ms": 0,
                    "slow_queries": 0,
                    "failed_queries": 0,
                    "operations": {}
                }
            
            total_queries = len(recent_metrics)
            successful_queries = [m for m in recent_metrics if m.success]
            failed_queries = [m for m in recent_metrics if not m.success]
            slow_queries = [m for m in recent_metrics if m.duration_ms > 1000]
            
            # Group by operation
            operations = {}
            for metric in recent_metrics:
                op = metric.operation
                if op not in operations:
                    operations[op] = {
                        "count": 0,
                        "total_duration_ms": 0,
                        "average_duration_ms": 0,
                        "max_duration_ms": 0,
                        "failures": 0
                    }
                
                operations[op]["count"] += 1
                operations[op]["total_duration_ms"] += metric.duration_ms
                operations[op]["max_duration_ms"] = max(
                    operations[op]["max_duration_ms"], 
                    metric.duration_ms
                )
                
                if not metric.success:
                    operations[op]["failures"] += 1
            
            # Calculate averages
            for op_stats in operations.values():
                if op_stats["count"] > 0:
                    op_stats["average_duration_ms"] = (
                        op_stats["total_duration_ms"] / op_stats["count"]
                    )
            
            average_duration = sum(m.duration_ms for m in successful_queries) / len(successful_queries) if successful_queries else 0
            average_checkout_time = sum(self.checkout_times) / len(self.checkout_times) if self.checkout_times else 0
            
            return {
                "time_period_hours": hours,
                "total_queries": total_queries,
                "successful_queries": len(successful_queries),
                "failed_queries": len(failed_queries),
                "slow_queries": len(slow_queries),
                "average_duration_ms": round(average_duration, 2),
                "average_checkout_time_ms": round(average_checkout_time, 2),
                "current_connections": self.connection_count,
                "failed_connections": self.failed_connections,
                "operations": operations
            }

class OptimizedDatabaseClient:
    """Optimized MongoDB client with enhanced features"""
    
    def __init__(self, connection_string: str, database_name: str = "online_evaluation"):
        self.connection_string = connection_string
        self.database_name = database_name
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.db: Optional[AgnosticDatabase] = None
        self.metrics_collector = DatabaseMetricsCollector()
        self.query_cache = {}
        self.cache_ttl = int(os.getenv("QUERY_CACHE_TTL_SECONDS", "300"))  # 5 minutes
        self._lock = asyncio.Lock()
        
        # Connection pool settings
        self.pool_settings = {
            "maxPoolSize": int(os.getenv("DB_MAX_POOL_SIZE", "50")),
            "minPoolSize": int(os.getenv("DB_MIN_POOL_SIZE", "5")),
            "maxIdleTimeMS": int(os.getenv("DB_MAX_IDLE_TIME_MS", "300000")),  # 5 minutes
            "serverSelectionTimeoutMS": int(os.getenv("DB_SERVER_SELECTION_TIMEOUT_MS", "5000")),
            "connectTimeoutMS": int(os.getenv("DB_CONNECT_TIMEOUT_MS", "10000")),
            "socketTimeoutMS": int(os.getenv("DB_SOCKET_TIMEOUT_MS", "30000")),
            "retryWrites": True,
            "retryReads": True
        }
    
    async def connect(self):
        """Establish database connection with monitoring"""
        try:
            # Setup monitoring
            command_monitor = CommandMonitor(self.metrics_collector)
            server_monitor = ServerMonitor(self.metrics_collector)
            
            monitoring.register(command_monitor)
            monitoring.register(server_monitor)
            
            # Create client with optimized settings
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                self.connection_string,
                **self.pool_settings
            )
            
            self.db = self.client[self.database_name]
            
            # Test connection
            await self.client.admin.command('ping')
            
            # Setup indexes
            await self._setup_indexes()
            
            logger.info(f"Connected to MongoDB with optimized settings: {self.pool_settings}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def _setup_indexes(self):
        """Setup recommended indexes for performance"""
        try:
            indexes = [
                # Users collection
                ("users", [
                    IndexModel([("login_id", 1)], unique=True),
                    IndexModel([("email", 1)], unique=True),
                    IndexModel([("role", 1)]),
                    IndexModel([("is_active", 1)]),
                    IndexModel([("created_at", -1)])
                ]),
                
                # Login attempts collection
                ("login_attempts", [
                    IndexModel([("login_id", 1)], unique=True),
                    IndexModel([("last_failed_attempt", -1)]),
                    IndexModel([("lockout_until", 1)])
                ]),
                
                # Evaluations collection
                ("evaluations", [
                    IndexModel([("evaluator_id", 1)]),
                    IndexModel([("template_id", 1)]),
                    IndexModel([("project_id", 1)]),
                    IndexModel([("created_at", -1)]),
                    IndexModel([("status", 1)]),
                    IndexModel([("evaluator_id", 1), ("status", 1)])
                ]),
                
                # Templates collection
                ("templates", [
                    IndexModel([("created_by", 1)]),
                    IndexModel([("category", 1)]),
                    IndexModel([("is_active", 1)]),
                    IndexModel([("created_at", -1)])
                ]),
                
                # Files collection
                ("files", [
                    IndexModel([("uploaded_by", 1)]),
                    IndexModel([("upload_date", -1)]),
                    IndexModel([("file_type", 1)]),
                    IndexModel([("project_id", 1)])
                ]),
                
                # Projects collection
                ("projects", [
                    IndexModel([("company_id", 1)]),
                    IndexModel([("created_by", 1)]),
                    IndexModel([("status", 1)]),
                    IndexModel([("created_at", -1)])
                ]),
                
                # Error logs collection
                ("error_logs", [
                    IndexModel([("timestamp", -1)]),
                    IndexModel([("severity", 1)]),
                    IndexModel([("category", 1)]),
                    IndexModel([("error_code", 1)]),
                    IndexModel([("user_id", 1), ("timestamp", -1)])
                ]),
                
                # User sessions collection
                ("user_sessions", [
                    IndexModel([("user_id", 1)]),
                    IndexModel([("session_id", 1)], unique=True),
                    IndexModel([("is_active", 1)]),
                    IndexModel([("expires_at", 1)])
                ])
            ]
            
            for collection_name, collection_indexes in indexes:
                collection = self.db[collection_name]
                await collection.create_indexes(collection_indexes)
                logger.info(f"Created indexes for {collection_name}")
        
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    @asynccontextmanager
    async def get_collection(self, collection_name: str):
        """Get collection with connection management"""
        start_time = time.time()
        
        try:
            collection = self.db[collection_name]
            yield collection
        finally:
            checkout_time = (time.time() - start_time) * 1000
            self.metrics_collector.add_checkout_time(checkout_time)
    
    async def find_with_cache(self, collection_name: str, filter_dict: Dict[str, Any], 
                            cache_key: str = None, **kwargs) -> List[Dict[str, Any]]:
        """Find documents with caching"""
        if not cache_key:
            cache_key = f"{collection_name}:{hash(str(sorted(filter_dict.items())))}"
        
        # Check cache
        if cache_key in self.query_cache:
            cached_data, cached_time = self.query_cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                return cached_data
        
        # Execute query
        async with self.get_collection(collection_name) as collection:
            cursor = collection.find(filter_dict, **kwargs)
            results = await cursor.to_list(None)
        
        # Cache results
        self.query_cache[cache_key] = (results, time.time())
        
        # Clean old cache entries
        if len(self.query_cache) > 1000:
            oldest_keys = sorted(
                self.query_cache.keys(), 
                key=lambda k: self.query_cache[k][1]
            )[:500]
            for key in oldest_keys:
                del self.query_cache[key]
        
        return results
    
    async def aggregate_with_optimization(self, collection_name: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute aggregation with optimization hints"""
        # Add optimization hints
        optimized_pipeline = pipeline.copy()
        
        # Add allowDiskUse for large aggregations
        async with self.get_collection(collection_name) as collection:
            cursor = collection.aggregate(optimized_pipeline, allowDiskUse=True)
            return await cursor.to_list(None)
    
    async def bulk_operation(self, collection_name: str, operations: List[Any], ordered: bool = False):
        """Execute bulk operations efficiently"""
        async with self.get_collection(collection_name) as collection:
            if operations:
                return await collection.bulk_write(operations, ordered=ordered)
    
    async def get_health_status(self) -> DatabaseHealth:
        """Get comprehensive database health status"""
        start_time = time.time()
        errors = []
        
        try:
            # Test basic connectivity
            await self.client.admin.command('ping')
            is_healthy = True
            
        except Exception as e:
            is_healthy = False
            errors.append(str(e))
        
        response_time_ms = (time.time() - start_time) * 1000
        
        # Get connection metrics
        try:
            # Get server status for connection info
            server_status = await self.client.admin.command('serverStatus')
            connections_info = server_status.get('connections', {})
            
            connection_metrics = ConnectionMetrics(
                active_connections=connections_info.get('current', 0),
                available_connections=connections_info.get('available', 0),
                total_connections=connections_info.get('totalCreated', 0),
                pool_utilization=(
                    connections_info.get('current', 0) / 
                    max(1, connections_info.get('available', 1) + connections_info.get('current', 0))
                ) * 100,
                failed_connections=self.metrics_collector.failed_connections,
                average_checkout_time_ms=sum(self.metrics_collector.checkout_times) / 
                                         len(self.metrics_collector.checkout_times) 
                                         if self.metrics_collector.checkout_times else 0
            )
        except Exception as e:
            errors.append(f"Connection metrics error: {str(e)}")
            connection_metrics = ConnectionMetrics(
                active_connections=0, available_connections=0, total_connections=0,
                pool_utilization=0, failed_connections=0, average_checkout_time_ms=0
            )
        
        # Get performance metrics
        performance_metrics = self.metrics_collector.get_performance_summary()
        
        return DatabaseHealth(
            is_healthy=is_healthy,
            response_time_ms=response_time_ms,
            connections=connection_metrics,
            recent_errors=errors,
            performance_metrics=performance_metrics,
            timestamp=datetime.utcnow()
        )
    
    async def backup_collection(self, collection_name: str, backup_path: str):
        """Backup a collection to JSON file"""
        try:
            backup_file = Path(backup_path) / f"{collection_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            
            async with self.get_collection(collection_name) as collection:
                cursor = collection.find({})
                documents = await cursor.to_list(None)
                
                # Convert ObjectIds to strings for JSON serialization
                for doc in documents:
                    if '_id' in doc:
                        doc['_id'] = str(doc['_id'])
                
                with open(backup_file, 'w') as f:
                    json.dump(documents, f, default=str, indent=2)
                
                logger.info(f"Backed up {len(documents)} documents from {collection_name} to {backup_file}")
                return str(backup_file)
        
        except Exception as e:
            logger.error(f"Backup failed for {collection_name}: {e}")
            raise
    
    async def restore_collection(self, collection_name: str, backup_file: str, drop_existing: bool = False):
        """Restore collection from JSON backup"""
        try:
            with open(backup_file, 'r') as f:
                documents = json.load(f)
            
            async with self.get_collection(collection_name) as collection:
                if drop_existing:
                    await collection.drop()
                
                if documents:
                    await collection.insert_many(documents)
                
                logger.info(f"Restored {len(documents)} documents to {collection_name}")
        
        except Exception as e:
            logger.error(f"Restore failed for {collection_name}: {e}")
            raise
    
    def clear_cache(self):
        """Clear query cache"""
        self.query_cache.clear()
        logger.info("Query cache cleared")

# Global database client instance
optimized_db_client = OptimizedDatabaseClient(
    connection_string=os.getenv("MONGO_URL", "mongodb://localhost:27017/online_evaluation")
)

async def initialize_database():
    """Initialize optimized database connection"""
    await optimized_db_client.connect()
    return optimized_db_client

async def cleanup_database():
    """Cleanup database connection"""
    await optimized_db_client.disconnect()

# Utility functions
async def get_database_statistics() -> Dict[str, Any]:
    """Get comprehensive database statistics"""
    health = await optimized_db_client.get_health_status()
    return {
        "health": asdict(health),
        "performance": optimized_db_client.metrics_collector.get_performance_summary(24),
        "cache_stats": {
            "cached_queries": len(optimized_db_client.query_cache),
            "cache_hit_rate": "N/A"  # Would need to track cache hits vs misses
        }
    }

async def backup_database(backup_path: str = "./backups") -> Dict[str, str]:
    """Backup all collections"""
    collections = ["users", "evaluations", "templates", "projects", "files", "companies"]
    backup_files = {}
    
    for collection in collections:
        try:
            backup_file = await optimized_db_client.backup_collection(collection, backup_path)
            backup_files[collection] = backup_file
        except Exception as e:
            logger.error(f"Failed to backup {collection}: {e}")
            backup_files[collection] = f"ERROR: {str(e)}"
    
    return backup_files