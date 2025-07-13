#!/usr/bin/env python3
"""
VALON PC Agent System - Production Deployment
Advanced AI Agent Platform with Real-time Web Interface
"""

import os
import json
import time
import threading
import requests
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging

# Production Configuration
class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'valon-agent-secret-key-2024'
    DEBUG = False
    TESTING = False
    
    # SocketIO Configuration
    SOCKETIO_ASYNC_MODE = 'eventlet'
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    
    # Agent Configuration
    AGENT_NAME = "VALON"
    VERSION = "2.1.0"
    MAX_USERS = 100
    MAX_TASKS = 1000

app = Flask(__name__)
app.config.from_object(ProductionConfig)

# Initialize SocketIO with production settings
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
                allowed_chars = set('0123456789+-*/().\s')
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

# Web Interface Template
WEB_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VALON Agent - AI Assistant Platform</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 1rem 2rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .header h1 {
            color: white;
            font-size: 2rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            color: rgba(255, 255, 255, 0.8);
            margin-top: 0.5rem;
        }
        
        .container {
            flex: 1;
            display: grid;
            grid-template-columns: 1fr 300px;
            gap: 2rem;
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
            width: 100%;
        }
        
        .main-panel {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            backdrop-filter: blur(4px);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }
        
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        .status-card, .users-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            backdrop-filter: blur(4px);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }
        
        .command-input {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .command-input input {
            flex: 1;
            padding: 1rem;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        
        .command-input input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .command-input button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .command-input button:hover {
            transform: translateY(-2px);
        }
        
        .terminal {
            background: #1a1a1a;
            border-radius: 8px;
            padding: 1.5rem;
            height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            color: #00ff00;
        }
        
        .terminal-line {
            margin: 0.5rem 0;
            padding: 0.25rem;
            border-radius: 4px;
        }
        
        .terminal-command {
            color: #ffff00;
        }
        
        .terminal-result {
            color: #00ff00;
            margin-left: 1rem;
        }
        
        .terminal-error {
            color: #ff6b6b;
            margin-left: 1rem;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #4ade80;
            margin-right: 0.5rem;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 0.5rem 0;
            padding: 0.5rem;
            background: rgba(103, 126, 234, 0.1);
            border-radius: 6px;
        }
        
        .quick-commands {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .quick-cmd {
            background: rgba(103, 126, 234, 0.1);
            border: 1px solid #667eea;
            color: #667eea;
            padding: 0.75rem;
            border-radius: 6px;
            cursor: pointer;
            text-align: center;
            transition: all 0.3s;
        }
        
        .quick-cmd:hover {
            background: #667eea;
            color: white;
        }
        
        @media (max-width: 768px) {
            .container {
                grid-template-columns: 1fr;
                padding: 1rem;
            }
            
            .command-input {
                flex-direction: column;
            }
            
            .quick-commands {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        .footer {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 1rem 2rem;
            text-align: center;
            color: rgba(255, 255, 255, 0.8);
            border-top: 1px solid rgba(255, 255, 255, 0.2);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 VALON Agent Platform</h1>
        <p>Advanced AI Assistant System - Real-time Command Processing</p>
    </div>
    
    <div class="container">
        <div class="main-panel">
            <div class="command-input">
                <input type="text" id="commandInput" placeholder="Enter command (e.g., system:memory, calculate:2+2, status)...">
                <button onclick="executeCommand()">Execute</button>
            </div>
            
            <div class="quick-commands">
                <div class="quick-cmd" onclick="quickCommand('status')">Status</div>
                <div class="quick-cmd" onclick="quickCommand('system:memory')">Memory</div>
                <div class="quick-cmd" onclick="quickCommand('system:users')">Users</div>
                <div class="quick-cmd" onclick="quickCommand('help')">Help</div>
            </div>
            
            <div class="terminal" id="terminal">
                <div class="terminal-line">VALON Agent System initialized...</div>
                <div class="terminal-line">Type commands above or use quick command buttons</div>
                <div class="terminal-line">Connected to real-time system ✓</div>
            </div>
        </div>
        
        <div class="sidebar">
            <div class="status-card">
                <h3><span class="status-indicator"></span>System Status</h3>
                <div class="metric">
                    <span>Status:</span>
                    <span id="agentStatus">Active</span>
                </div>
                <div class="metric">
                    <span>Commands:</span>
                    <span id="commandCount">0</span>
                </div>
                <div class="metric">
                    <span>Tasks:</span>
                    <span id="taskCount">0</span>
                </div>
                <div class="metric">
                    <span>Version:</span>
                    <span>v2.1.0</span>
                </div>
            </div>
            
            <div class="users-card">
                <h3>👥 Active Users</h3>
                <div class="metric">
                    <span>Connected:</span>
                    <span id="userCount">1</span>
                </div>
                <div class="metric">
                    <span>Sessions:</span>
                    <span id="sessionCount">1</span>
                </div>
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p>VALON Agent © 2024 | Real-time AI Assistant Platform | 
        <a href="/api/status" style="color: rgba(255,255,255,0.8);">API Status</a></p>
    </div>

    <script>
        // Initialize Socket.IO connection
        const socket = io();
        
        // Global variables
        let commandCount = 0;
        let taskCount = 0;
        
        // Connect to server
        socket.on('connect', function() {
            console.log('Connected to VALON Agent');
            addToTerminal('Connected to VALON Agent server ✓', 'result');
            updateStatus();
        });
        
        // Handle command results
        socket.on('command_result', function(data) {
            const timestamp = new Date().toLocaleTimeString();
            addToTerminal(`[${timestamp}] Command: ${data.command}`, 'command');
            
            if (data.success) {
                if (typeof data.result === 'object') {
                    addToTerminal(JSON.stringify(data.result, null, 2), 'result');
                } else {
                    addToTerminal(data.result, 'result');
                }
            } else {
                addToTerminal(`Error: ${data.result}`, 'error');
            }
            
            commandCount++;
            document.getElementById('commandCount').textContent = commandCount;
        });
        
        // Handle status updates
        socket.on('status_update', function(data) {
            document.getElementById('agentStatus').textContent = data.status || 'Active';
            document.getElementById('taskCount').textContent = data.task_count || 0;
            document.getElementById('userCount').textContent = data.user_count || 1;
            document.getElementById('sessionCount').textContent = data.session_count || 1;
        });
        
        // Execute command function
        function executeCommand() {
            const input = document.getElementById('commandInput');
            const command = input.value.trim();
            
            if (command) {
                socket.emit('execute_command', {command: command});
                input.value = '';
            }
        }
        
        // Quick command function
        function quickCommand(cmd) {
            document.getElementById('commandInput').value = cmd;
            executeCommand();
        }
        
        // Add line to terminal
        function addToTerminal(text, type = 'result') {
            const terminal = document.getElementById('terminal');
            const line = document.createElement('div');
            line.className = `terminal-line terminal-${type}`;
            line.textContent = text;
            terminal.appendChild(line);
            terminal.scrollTop = terminal.scrollHeight;
        }
        
        // Handle Enter key
        document.getElementById('commandInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                executeCommand();
            }
        });
        
        // Update status periodically
        function updateStatus() {
            socket.emit('get_status');
        }
        
        setInterval(updateStatus, 30000); // Update every 30 seconds
        
        // Handle disconnect
        socket.on('disconnect', function() {
            addToTerminal('Disconnected from server', 'error');
        });
    </script>
</body>
</html>
"""

# Routes
@app.route('/')
def dashboard():
    """Main dashboard route"""
    return render_template_string(WEB_TEMPLATE)

@app.route('/api/status')
def api_status():
    """API status endpoint"""
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
    """API command execution endpoint"""
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
    """API tasks endpoint"""
    return jsonify({
        "tasks": agent.tasks[-10:],  # Return last 10 tasks
        "total_tasks": len(agent.tasks)
    })

# Socket.IO Events
@socketio.on('connect')
def handle_connect():
    """Handle new client connection"""
    user_id = request.sid
    agent.users[user_id] = {
        "connected_at": datetime.now(),
        "ip": request.remote_addr,
        "commands": 0
    }
    agent.active_sessions += 1
    
    logger.info(f"User {user_id} connected from {request.remote_addr}")
    
    # Send welcome message
    emit('status_update', {
        "status": agent.status,
        "user_count": len(agent.users),
        "session_count": agent.active_sessions,
        "task_count": len(agent.tasks)
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    user_id = request.sid
    if user_id in agent.users:
        del agent.users[user_id]
        agent.active_sessions = max(0, agent.active_sessions - 1)
        logger.info(f"User {user_id} disconnected")

@socketio.on('execute_command')
def handle_execute_command(data):
    """Handle command execution via WebSocket"""
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
    """Handle status request"""
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

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

# Main execution
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    if os.environ.get('FLASK_ENV') == 'production':
        # Production mode
        logger.info(f"Starting VALON Agent in production mode on port {port}")
        socketio.run(app, host='0.0.0.0', port=port, debug=False)
    else:
        # Development mode
        logger.info(f"Starting VALON Agent in development mode on port {port}")
        socketio.run(app, host='0.0.0.0', port=port, debug=True)
