#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket Notification Service
Real-time notifications for the Online Evaluation System
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import logging
import asyncio
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time notifications"""
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Store connection metadata
        self.connection_metadata: Dict[WebSocket, Dict] = {}
        # Store room-based connections (for projects, teams, etc.)
        self.rooms: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, connection_type: str = "general"):
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        # Add to user connections
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        
        # Store metadata
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "connection_type": connection_type,
            "connected_at": datetime.utcnow(),
            "connection_id": str(uuid.uuid4())
        }
        
        logger.info(f"✅ WebSocket connected: User {user_id}, Type: {connection_type}")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "message": "실시간 알림이 활성화되었습니다",  # Korean: "Real-time notifications are activated"
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.connection_metadata:
            user_id = self.connection_metadata[websocket]["user_id"]
            
            # Remove from user connections
            if user_id in self.active_connections:
                self.active_connections[user_id] = [
                    conn for conn in self.active_connections[user_id] 
                    if conn != websocket
                ]
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # Remove from all rooms
            for room_connections in self.rooms.values():
                room_connections.discard(websocket)
            
            # Remove metadata
            del self.connection_metadata[websocket]
            
            logger.info(f"❌ WebSocket disconnected: User {user_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def send_user_message(self, message: dict, user_id: str):
        """Send message to all connections of a specific user"""
        if user_id in self.active_connections:
            disconnected_connections = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending user message: {e}")
                    disconnected_connections.append(connection)
            
            # Clean up disconnected connections
            for conn in disconnected_connections:
                self.disconnect(conn)
    
    async def join_room(self, websocket: WebSocket, room_id: str):
        """Add connection to a room (for project/team notifications)"""
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(websocket)
        logger.info(f"📋 User joined room: {room_id}")
    
    async def leave_room(self, websocket: WebSocket, room_id: str):
        """Remove connection from a room"""
        if room_id in self.rooms:
            self.rooms[room_id].discard(websocket)
            if not self.rooms[room_id]:
                del self.rooms[room_id]
        logger.info(f"📤 User left room: {room_id}")
    
    async def broadcast_to_room(self, message: dict, room_id: str):
        """Send message to all connections in a room"""
        if room_id in self.rooms:
            disconnected_connections = []
            for connection in self.rooms[room_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error broadcasting to room: {e}")
                    disconnected_connections.append(connection)
            
            # Clean up disconnected connections
            for conn in disconnected_connections:
                self.disconnect(conn)
    
    async def broadcast_to_all(self, message: dict):
        """Send message to all connected users"""
        all_connections = []
        for connections in self.active_connections.values():
            all_connections.extend(connections)
        
        disconnected_connections = []
        for connection in all_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to all: {e}")
                disconnected_connections.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected_connections:
            self.disconnect(conn)
    
    def get_active_users(self) -> List[str]:
        """Get list of currently connected user IDs"""
        return list(self.active_connections.keys())
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())

class NotificationService:
    """Service for creating and sending various types of notifications"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
    
    async def send_assignment_notification(self, user_id: str, assignment_data: dict):
        """Send assignment-related notification"""
        message = {
            "type": "assignment_update",
            "title": "새로운 평가 과제",  # Korean: "New Evaluation Assignment"
            "message": f"새로운 과제가 할당되었습니다: {assignment_data.get('title', '')}",
            "data": assignment_data,
            "timestamp": datetime.utcnow().isoformat(),
            "priority": "high"
        }
        await self.connection_manager.send_user_message(message, user_id)
    
    async def send_evaluation_complete_notification(self, user_id: str, evaluation_data: dict):
        """Send evaluation completion notification"""
        message = {
            "type": "evaluation_complete",
            "title": "평가 완료",  # Korean: "Evaluation Complete"
            "message": f"평가가 완료되었습니다: {evaluation_data.get('title', '')}",
            "data": evaluation_data,
            "timestamp": datetime.utcnow().isoformat(),
            "priority": "medium"
        }
        await self.connection_manager.send_user_message(message, user_id)
    
    async def send_deadline_reminder(self, user_id: str, deadline_data: dict):
        """Send deadline reminder notification"""
        message = {
            "type": "deadline_reminder",
            "title": "마감일 알림",  # Korean: "Deadline Reminder"
            "message": f"마감일이 임박했습니다: {deadline_data.get('title', '')}",
            "data": deadline_data,
            "timestamp": datetime.utcnow().isoformat(),
            "priority": "urgent"
        }
        await self.connection_manager.send_user_message(message, user_id)
    
    async def send_system_maintenance_notification(self, message_text: str):
        """Send system maintenance notification to all users"""
        message = {
            "type": "system_maintenance",
            "title": "시스템 점검 안내",  # Korean: "System Maintenance Notice"
            "message": message_text,
            "timestamp": datetime.utcnow().isoformat(),
            "priority": "info"
        }
        await self.connection_manager.broadcast_to_all(message)
    
    async def send_project_update_notification(self, project_id: str, update_data: dict):
        """Send project update notification to project members"""
        message = {
            "type": "project_update",
            "title": "프로젝트 업데이트",  # Korean: "Project Update"
            "message": f"프로젝트가 업데이트되었습니다: {update_data.get('title', '')}",
            "data": update_data,
            "timestamp": datetime.utcnow().isoformat(),
            "priority": "medium"
        }
        await self.connection_manager.broadcast_to_room(message, f"project:{project_id}")

# Global instances
connection_manager = ConnectionManager()
notification_service = NotificationService(connection_manager)
