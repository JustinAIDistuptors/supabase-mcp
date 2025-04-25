#!/usr/bin/env python3
"""
Supabase MCP Server
This file implements a simple MCP server for supabase operations.
"""

import os
import json
import logging
import uuid
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("supabase-mcp")

# Create FastAPI app
app = FastAPI(title="Supabase MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for tables
tables = {
    "users": [
        {"id": "1", "name": "John Doe", "email": "john@example.com"},
        {"id": "2", "name": "Jane Smith", "email": "jane@example.com"}
    ],
    "posts": [
        {"id": "1", "title": "First Post", "content": "Hello World", "user_id": "1"},
        {"id": "2", "title": "Second Post", "content": "Another post", "user_id": "2"}
    ],
    "comments": [
        {"id": "1", "post_id": "1", "user_id": "2", "content": "Great post!"},
        {"id": "2", "post_id": "1", "user_id": "1", "content": "Thanks!"}
    ]
}

# MCP endpoint
@app.post("/mcp/{function_name}")
async def handle_mcp_request(function_name: str, request: Request):
    """Handle MCP request"""
    try:
        # Parse request body
        body = await request.body()
        parameters = json.loads(body) if body else {}
        
        # Log the request
        logger.info(f"Received request for function: {function_name}")
        logger.info(f"Parameters: {parameters}")
        
        # Handle different functions
        if function_name == "query":
            table_name = parameters.get("table")
            filters = parameters.get("filters", {})
            
            if not table_name:
                return {"error": "table parameter is required"}
            
            if table_name not in tables:
                return {"error": f"Table {table_name} not found"}
            
            # Apply filters if any
            results = tables[table_name]
            if filters:
                filtered_results = []
                for item in results:
                    match = True
                    for key, value in filters.items():
                        if key not in item or item[key] != value:
                            match = False
                            break
                    if match:
                        filtered_results.append(item)
                results = filtered_results
            
            result = {"data": results}
        
        elif function_name == "insert":
            table_name = parameters.get("table")
            records = parameters.get("records", [])
            
            if not table_name:
                return {"error": "table parameter is required"}
            
            if not records:
                return {"error": "records parameter is required"}
            
            if table_name not in tables:
                tables[table_name] = []
            
            inserted_ids = []
            for record in records:
                record_id = record.get("id", str(uuid.uuid4()))
                record["id"] = record_id
                tables[table_name].append(record)
                inserted_ids.append(record_id)
            
            result = {"ids": inserted_ids, "success": True}
        
        elif function_name == "update":
            table_name = parameters.get("table")
            record_id = parameters.get("id")
            updates = parameters.get("updates", {})
            
            if not table_name:
                return {"error": "table parameter is required"}
            
            if not record_id:
                return {"error": "id parameter is required"}
            
            if not updates:
                return {"error": "updates parameter is required"}
            
            if table_name not in tables:
                return {"error": f"Table {table_name} not found"}
            
            # Find and update the record
            for i, record in enumerate(tables[table_name]):
                if record.get("id") == record_id:
                    for key, value in updates.items():
                        tables[table_name][i][key] = value
                    result = {"success": True}
                    break
            else:
                result = {"error": f"Record with id {record_id} not found in table {table_name}"}
        
        elif function_name == "delete":
            table_name = parameters.get("table")
            record_id = parameters.get("id")
            
            if not table_name:
                return {"error": "table parameter is required"}
            
            if not record_id:
                return {"error": "id parameter is required"}
            
            if table_name not in tables:
                return {"error": f"Table {table_name} not found"}
            
            # Find and delete the record
            for i, record in enumerate(tables[table_name]):
                if record.get("id") == record_id:
                    del tables[table_name][i]
                    result = {"success": True}
                    break
            else:
                result = {"error": f"Record with id {record_id} not found in table {table_name}"}
        
        elif function_name == "list_tables":
            result = {"tables": list(tables.keys())}
        
        else:
            return {"error": f"Function {function_name} not supported"}
        
        logger.info(f"Result: {result}")
        return result
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return {"error": "Invalid JSON in request body"}
    except Exception as e:
        logger.error(f"Error handling request: {str(e)}")
        return {"error": str(e)}

@app.get("/")
async def root():
    """Root endpoint that returns information about the server"""
    return {
        "name": "Supabase MCP Server",
        "version": "1.0.0",
        "description": "MCP server for supabase operations",
        "functions": ["query", "insert", "update", "delete", "list_tables"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    logger.info(f"Starting Supabase MCP Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
