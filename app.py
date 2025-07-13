#!/usr/bin/env python3
"""
VALON PC Agent System - Cloud Deployment (Render.com/Python 3.13)
Advanced AI Agent Platform with Real-time Web Interface (Werkzeug/Threading)
"""

import os
import json
import time
import threading
import requests
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit
import logging

# Production Configuration
class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'valon-agent-secret-key-2024'
    DEBUG = False
    TESTING = False
    # SocketIO Configuration (NO eventlet/gevent)
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    # Agent Configuration
    AGENT_NAME = "VALON"
    VERSION = "2.1.0"
    MAX_USERS = 100
    MAX_TASKS = 1000

app = Flask(__name__)
app.config.from_object(ProductionConfig)

# Initialize SocketIO (NO eventlet/gevent, use default 'threading')
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state management
class VALONAgent:
    def __init__(self):
        self.status = "Active"
        self.tasks = []
        self.users = {}
        self.memory = {
            "commands_executed": 0,
            "uptime_start": datetime.now(),
            "system_info": "VALON Agent v2.1.0 - Production"
        }
        self.active_sessions = 0

    def add_task(self, task):
        if len(self.tasks) >= ProductionConfig.MAX_TASKS:
            self.tasks.pop(0)  # Remove oldest task

        task_obj = {
            "id": len(self.tasks) + 1,
            "command": task.get("command", ""),
            "status": "pending",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": task.get("user", "anonymous"),
            "result": None
        }
        self.tasks.append(task_obj)
        return task_obj

    def execute_command(self, command, user_id="anonymous"):
        """Enhanced command execution with production error handling"""
        try:
            self.memory["commands_executed"] += 1

            # Command processing logic
            if command.startswith("system:"):
                return self._handle_system_command(command, user_id)
            elif command.startswith("web:"):
                return self._handle_web_command(command, user_id)
            elif command.startswith("calculate:"):
                return self._handle_calculate_command(command, user_id)
            elif command.startswith("status"):
                return self._handle_status_command(command, user_id)
            elif command.startswith("help"):
                return self._handle_help_command(command, user_id)
            else:
                return {
                    "success": True,
                    "result": f"Command '{command}' processed by VALON Agent",
                    "type": "general",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        except Exception as e:
            logger.error(f"Command execution error: {str(e)}")
            return {
                "success": False,
                "result": f"Error processing command: {str(e)}",
                "type": "error",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    def _handle_system_command(self, command, user_id):
        cmd_parts = command.split(":", 1)
        if len(cmd_parts) > 1:
            sub_cmd = cmd_parts[1].strip()

            if sub_cmd == "memory":
                uptime = datetime.now() - self.memory["uptime_start"]
                return {
                    "success": True,
                    "result": {
                        "commands_executed": self.memory["commands_executed"],
                        "uptime": str(uptime),
                        "active_users": len(self.users),
                        "active_sessions": self.active_sessions,
                        "total_tasks": len(self.tasks),
                        "system_info": self.memory["system_info"]
                    },
                    "type": "system"
                }
            elif sub_cmd == "users":
                return {
                    "success": True,
                    "result": {
                        "total_users": len(self.users),
                        "active_sessions": self.active_sessions,
                        "user_list": list(self.users.keys())
                    },
                    "type": "system"
                }

        return {
            "success": True,
            "result": "System command executed",
            "type": "system"
        }

    def _handle_web_command(self, command, user_id):
        cmd_parts = command.split(":", 1)
        if len(cmd_parts) > 1:
            sub_cmd = cmd_parts[1].strip()

            if sub_cmd == "users":
                return {
                    "success": True,
                    "result": f"Web users: {len(self.users)} active sessions",
                    "type": "web"
                }
            elif sub_cmd.startswith("fetch "):
                url = sub_cmd[6:].strip()
                try:
                    response = requests.get(url, timeout=10)
                    return {
                        "success": True,
                        "result": f"Fetched {url} - Status: {response.status_code}",
                        "type": "web"
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "result": f"Failed to fetch {url}: {str(e)}",
                        "type": "web"
                    }

        return {
            "success": True,
            "result": "Web command executed",
            "type": "web"
        }

    def _handle_calculate_command(self, command, user_id):
        cmd_parts = command.split(":", 1)
        if len(cmd_parts) > 1:
            expression = cmd_parts[1].strip()
            try:
                # Safe evaluation of mathematical expressions
                allowed_chars = set('0123456789+-*/(). \t\n')
                if all(c in allowed_chars for c in expression):
                    result = eval(expression)
                    return {
                        "success": True,
                        "result": f"{expression} = {result}",
                        "type": "calculation"
                    }
                else:
                    return {
                        "success": False,
                        "result": "Invalid characters in expression",
                        "type": "calculation"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "result": f"Calculation error: {str(e)}",
                    "type": "calculation"
                }

        return {
            "success": False,
            "result": "No expression provided",
            "type": "calculation"
        }

    def _handle_status_command(self, command, user_id):
        uptime = datetime.now() - self.memory["uptime_start"]
        return {
            "success": True,
            "result": {
                "status": self.status,
                "uptime": str(uptime),
                "commands_executed": self.memory["commands_executed"],
                "active_users": len(self.users),
                "total_tasks": len(self.tasks),
                "version": ProductionConfig.VERSION
            },
            "type": "status"
        }

    def _handle_help_command(self, command, user_id):
        help_text = """
VALON Agent Commands:
- system:memory - Show system memory and stats
- system:users - Show user information
- web:users - Show web user count
- web:fetch [url] - Fetch a web page
- calculate:[expression] - Perform calculations
- status - Show agent status
- help - Show this help message
        """
        return {
            "success": True,
            "result": help_text.strip(),
            "type": "help"
        }

# Initialize VALON Agent
agent = VALONAgent()

# --------------------------------------
# ------------- WEB_TEMPLATE -----------
# --------------------------------------
WEB_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<!-- ... (your dashboard HTML here, as before) ... -->
<body>
    <div class="header">
        <h1>🤖 VALON Agent Platform</h1>
        <p>Advanced AI Assistant System - Real-time Command Processing</p>
    </div>
    <!-- Rest of your HTML goes here. Omitted for brevity. -->
</body>
</html>
"""

# ------------- ROUTES & SOCKETIO --------------
@app.route('/')
def dashboard():
    return render_template_string(WEB_TEMPLATE)

@app.route('/api/status')
def api_status():
    uptime = datetime.now() - agent.memory["uptime_start"]
    return jsonify({
        "status": "online",
        "agent_status": agent.status,
        "uptime": str(uptime),
        "commands_executed": agent.memory["commands_executed"],
        "active_users": len(agent.users),
        "active_sessions": agent.active_sessions,
        "total_tasks": len(agent.tasks),
        "version": ProductionConfig.VERSION,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/execute', methods=['POST'])
def api_execute():
    try:
        data = request.get_json()
        command = data.get('command', '')
        user_id = request.remote_addr

        if not command:
            return jsonify({"success": False, "error": "No command provided"}), 400

        # Add task and execute
        task = agent.add_task({"command": command, "user": user_id})
        result = agent.execute_command(command, user_id)

        # Update task status
        task["status"] = "completed" if result["success"] else "failed"
        task["result"] = result

        return jsonify({
            "success": True,
            "task_id": task["id"],
            "result": result
        })
    except Exception as e:
        logger.error(f"API execute error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/tasks')
def api_tasks():
    return jsonify({
        "tasks": agent.tasks[-10:],  # Return last 10 tasks
        "total_tasks": len(agent.tasks)
    })

@socketio.on('connect')
def handle_connect():
    user_id = request.sid
    agent.users[user_id] = {
        "connected_at": datetime.now(),
        "ip": request.remote_addr,
        "commands": 0
    }
    agent.active_sessions += 1
    logger.info(f"User {user_id} connected from {request.remote_addr}")
    emit('status_update', {
        "status": agent.status,
        "user_count": len(agent.users),
        "session_count": agent.active_sessions,
        "task_count": len(agent.tasks)
    })

@socketio.on('disconnect')
def handle_disconnect():
    user_id = request.sid
    if user_id in agent.users:
        del agent.users[user_id]
        agent.active_sessions = max(0, agent.active_sessions - 1)
        logger.info(f"User {user_id} disconnected")

@socketio.on('execute_command')
def handle_execute_command(data):
    try:
        command = data.get('command', '')
        user_id = request.sid

        if not command:
            emit('command_result', {
                "success": False,
                "command": command,
                "result": "No command provided"
            })
            return

        # Update user command count
        if user_id in agent.users:
            agent.users[user_id]["commands"] += 1

        # Add task and execute
        task = agent.add_task({"command": command, "user": user_id})
        result = agent.execute_command(command, user_id)

        # Update task status
        task["status"] = "completed" if result["success"] else "failed"
        task["result"] = result

        # Send result back to client
        emit('command_result', {
            "success": result["success"],
            "command": command,
            "result": result["result"],
            "type": result.get("type", "general"),
            "task_id": task["id"]
        })

        # Broadcast status update to all clients
        socketio.emit('status_update', {
            "status": agent.status,
            "user_count": len(agent.users),
            "session_count": agent.active_sessions,
            "task_count": len(agent.tasks)
        })

    except Exception as e:
        logger.error(f"Command execution error: {str(e)}")
        emit('command_result', {
            "success": False,
            "command": data.get('command', ''),
            "result": f"Error: {str(e)}"
        })

@socketio.on('get_status')
def handle_get_status():
    uptime = datetime.now() - agent.memory["uptime_start"]
    emit('status_update', {
        "status": agent.status,
        "uptime": str(uptime),
        "commands_executed": agent.memory["commands_executed"],
        "user_count": len(agent.users),
        "session_count": agent.active_sessions,
        "task_count": len(agent.tasks),
        "version": ProductionConfig.VERSION
    })

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting VALON Agent on port {port} (Werkzeug, threading mode, allow_unsafe_werkzeug=True)")
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
