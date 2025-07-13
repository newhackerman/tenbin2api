#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件管理API端点
用于支持chat.html的设置保存功能
"""

import json
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# 配置文件路径
CONFIG_FILE = 'tenbin_config.json'
SESSIONS_FILE = 'tenbin_sessions.json'
TENBIN_FILE = 'tenbin.json'  # 第三方服务凭证文件

# 数据模型
class ConfigData(BaseModel):
    session_id: str = None
    api_base: str = None
    api_key: str = None
    system_prompt: str = None
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30000
    retry_interval: int = 5000
    theme: str = 'default'
    auto_save: bool = True

class SessionData(BaseModel):
    session_id: str
    created_at: str = None
    updated_at: str = None

def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
    return {}

def save_config(config_data):
    """保存配置文件"""
    try:
        config = load_config()
        config.update(config_data)
        config['updated_at'] = datetime.now().isoformat()
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存配置文件失败: {e}")
        return False

def load_sessions():
    """加载会话数据"""
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载会话文件失败: {e}")
    return []

def save_session(session_data):
    """保存会话数据"""
    try:
        sessions = load_sessions()
        
        # 查找现有会话
        existing_index = -1
        for i, session in enumerate(sessions):
            if session.get('session_id') == session_data['session_id']:
                existing_index = i
                break
        
        session_entry = {
            'session_id': session_data['session_id'],
            'created_at': session_data.get('created_at', datetime.now().isoformat()),
            'updated_at': datetime.now().isoformat()
        }
        
        if existing_index >= 0:
            sessions[existing_index] = session_entry
        else:
            sessions.append(session_entry)
        
        with open(SESSIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存会话文件失败: {e}")
        return False

def load_tenbin_credentials():
    """加载 tenbin.json 凭证文件"""
    if os.path.exists(TENBIN_FILE):
        try:
            with open(TENBIN_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载 tenbin.json 失败: {e}")
    return []

def save_tenbin_session_id(session_id):
    """保存 session_id 到 tenbin.json 文件"""
    try:
        # 加载现有数据
        tenbin_data = load_tenbin_credentials()
        
        # 查找是否已存在相同的 session_id
        existing_index = -1
        for i, item in enumerate(tenbin_data):
            if item.get('session_id') == session_id:
                existing_index = i
                break
        
        session_entry = {"session_id": session_id}
        
        if existing_index >= 0:
            # 更新现有条目
            tenbin_data[existing_index] = session_entry
        else:
            # 添加新条目
            tenbin_data.append(session_entry)
        
        # 保存到文件
        with open(TENBIN_FILE, 'w', encoding='utf-8') as f:
            json.dump(tenbin_data, f, ensure_ascii=False, indent=4)
        
        print(f"Session ID '{session_id}' 已保存到 tenbin.json")
        return True
    except Exception as e:
        print(f"保存到 tenbin.json 失败: {e}")
        return False

# 创建路由器
config_router = APIRouter(prefix="/config", tags=["config"])

@config_router.get("/")
async def get_config():
    """获取当前配置"""
    config = load_config()
    return {"status": "success", "data": config}

@config_router.post("/")
async def update_config(config: ConfigData):
    """更新配置"""
    config_dict = config.dict(exclude_unset=True)
    success = save_config(config_dict)
    
    if success:
        return {"status": "success", "message": "配置已保存"}
    else:
        raise HTTPException(status_code=500, detail="保存配置失败")

@config_router.get("/sessions")
async def get_sessions():
    """获取会话列表"""
    sessions = load_sessions()
    return {"status": "success", "data": sessions}

@config_router.post("/sessions")
async def update_session(session: SessionData):
    """更新会话"""
    session_dict = session.dict(exclude_unset=True)
    success = save_session(session_dict)
    
    if success:
        return {"status": "success", "message": "会话已保存"}
    else:
        raise HTTPException(status_code=500, detail="保存会话失败")

@config_router.post("/tenbin")
async def save_tenbin_session(session: SessionData):
    """保存 Tenbin Session ID 到 tenbin.json"""
    if not session.session_id:
        raise HTTPException(status_code=400, detail="session_id 不能为空")
    
    success = save_tenbin_session_id(session.session_id)
    
    if success:
        return {"status": "success", "message": f"Tenbin Session ID '{session.session_id}' 已保存到 tenbin.json"}
    else:
        raise HTTPException(status_code=500, detail="保存到 tenbin.json 失败")

@config_router.get("/tenbin")
async def get_tenbin_credentials():
    """获取 tenbin.json 凭证"""
    credentials = load_tenbin_credentials()
    return {"status": "success", "data": credentials}

if __name__ == "__main__":
    # 测试脚本
    print("配置管理模块测试")
    
    # 测试保存配置
    test_config = {
        "session_id": "test_session_123",
        "api_base": "http://127.0.0.1:8401",
        "theme": "dark"
    }
    
    if save_config(test_config):
        print("配置保存测试成功")
    else:
        print("配置保存测试失败")
    
    # 测试加载配置
    loaded_config = load_config()
    print(f"加载的配置: {loaded_config}")
    
    # 测试保存会话
    test_session = {
        "session_id": "session_test_456"
    }
    
    if save_session(test_session):
        print("会话保存测试成功")
    else:
        print("会话保存测试失败")
    
    # 测试加载会话
    loaded_sessions = load_sessions()
    print(f"加载的会话: {loaded_sessions}")