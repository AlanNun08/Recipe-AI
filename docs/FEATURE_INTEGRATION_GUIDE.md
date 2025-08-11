# Feature Integration Guide

## Overview
This guide provides step-by-step instructions for integrating new features into the AI Chef application. It covers frontend components, backend APIs, database schema updates, and testing strategies.

## Table of Contents
1. [Integration Workflow](#integration-workflow)
2. [Frontend Component Integration](#frontend-component-integration)
3. [Backend API Development](#backend-api-development)
4. [Database Schema Updates](#database-schema-updates)
5. [Third-Party Service Integration](#third-party-service-integration)
6. [Testing New Features](#testing-new-features)
7. [Deployment Considerations](#deployment-considerations)
8. [Common Integration Patterns](#common-integration-patterns)

## Integration Workflow

### Step-by-Step Process
1. **Planning Phase**
   - Define feature requirements
   - Design API endpoints
   - Plan database changes
   - Identify dependencies

2. **Development Phase**
   - Backend API implementation
   - Frontend component development
   - Database migrations
   - Testing implementation

3. **Integration Phase**
   - Component integration
   - End-to-end testing
   - Performance validation
   - Security review

4. **Deployment Phase**
   - Staging deployment
   - Production deployment
   - Monitoring setup
   - Documentation updates

## Frontend Component Integration

### 1. Creating a New Screen Component

#### Step 1: Component Structure
```javascript
// /frontend/src/components/NewFeatureScreen.js
import React, { useState, useEffect, useCallback } from 'react';

const API = process.env.REACT_APP_BACKEND_URL;

/**
 * NewFeatureScreen Component
 * 
 * @param {Object} props - Component props
 * @param {Object} props.user - Current user object
 * @param {Function} props.onBack - Navigation back function
 * @param {Function} props.showNotification - Notification display function
 */
function NewFeatureScreen({ user, onBack, showNotification }) {
  // State management
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Data fetching
  const fetchData = useCallback(async () => {
    if (!user?.id) {
      setError('User not authenticated');
      setIsLoading(false);
      return;
    }
    
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch(`${API}/api/new-feature/${user.id}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Failed to load data: ${response.status}`);
      }
      
      const result = await response.json();
      setData(result.data || []);
      
    } catch (error) {
      console.error('Error fetching data:', error);
      setError(error.message);
      showNotification(`Error: ${error.message}`, 'error');
    } finally {
      setIsLoading(false);
    }
  }, [user?.id, showNotification]);
  
  useEffect(() => {
    fetchData();
  }, [fetchData]);
  
  // Event handlers
  const handleAction = async (item) => {
    try {
      const response = await fetch(`${API}/api/new-feature/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: user.id,
          item_id: item.id
        })
      });
      
      if (!response.ok) {
        throw new Error('Action failed');
      }
      
      showNotification('Action completed successfully', 'success');
      fetchData(); // Refresh data
      
    } catch (error) {
      showNotification(`Action failed: ${error.message}`, 'error');
    }
  };
  
  // Render functions
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-lg p-8 text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <h2 className="text-xl font-bold text-gray-800">Loading New Feature</h2>
          <p className="text-gray-600">Please wait...</p>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 text-center max-w-md">
          <h2 className="text-2xl font-bold text-red-600 mb-4">Error Loading Feature</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <div className="flex gap-4 justify-center">
            <button
              onClick={fetchData}
              className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
            >
              Retry
            </button>
            <button
              onClick={onBack}
              className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
            >
              Go Back
            </button>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={onBack}
            className="flex items-center text-blue-700 hover:text-blue-800 font-medium mb-6"
          >
            <span className="mr-2">←</span>
            Back to Dashboard
          </button>
          
          <div className="text-center bg-white rounded-lg shadow-lg p-8">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
              New Feature
            </h1>
            <p className="text-lg text-gray-600">
              Description of your new feature
            </p>
          </div>
        </div>
        
        {/* Content */}
        {data.length === 0 ? (
          <div className="text-center py-12">
            <div className="bg-white rounded-lg shadow-lg p-8">
              <div className="text-4xl mb-4">📝</div>
              <h3 className="text-xl font-bold text-gray-800 mb-4">No Data Found</h3>
              <p className="text-gray-600">No data available for this feature yet.</p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data.map(item => (
              <div key={item.id} className="bg-white rounded-lg shadow-lg p-6">
                <h3 className="text-lg font-bold mb-2">{item.title}</h3>
                <p className="text-gray-600 mb-4">{item.description}</p>
                <button
                  onClick={() => handleAction(item)}
                  className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded"
                >
                  Action
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default NewFeatureScreen;
```

#### Step 2: App.js Integration
```javascript
// Add import to App.js
import NewFeatureScreen from './components/NewFeatureScreen';

// Add to switch statement
case 'new-feature':
  return <NewFeatureScreen 
    user={user}
    onBack={() => setCurrentScreen('dashboard')}
    showNotification={showNotification}
  />;

// Add navigation trigger (in dashboard or menu)
<button onClick={() => setCurrentScreen('new-feature')}>
  New Feature
</button>
```

### 2. Creating Reusable Sub-Components

#### Modal Component Example
```javascript
// /frontend/src/components/common/Modal.js
import React from 'react';

function Modal({ isOpen, onClose, title, children, size = 'md' }) {
  if (!isOpen) return null;
  
  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-2xl',
    lg: 'max-w-4xl',
    xl: 'max-w-6xl'
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className={`bg-white rounded-lg shadow-lg ${sizeClasses[size]} w-full mx-4 max-h-screen overflow-y-auto`}>
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-xl font-bold">{title}</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>
        <div className="p-6">
          {children}
        </div>
      </div>
    </div>
  );
}

export default Modal;
```

#### Form Component Example
```javascript
// /frontend/src/components/common/Form.js
import React, { useState } from 'react';

function Form({ fields, onSubmit, submitText = 'Submit', isLoading = false }) {
  const [formData, setFormData] = useState({});
  const [errors, setErrors] = useState({});
  
  const handleChange = (fieldName, value) => {
    setFormData(prev => ({ ...prev, [fieldName]: value }));
    if (errors[fieldName]) {
      setErrors(prev => ({ ...prev, [fieldName]: null }));
    }
  };
  
  const validateForm = () => {
    const newErrors = {};
    
    fields.forEach(field => {
      if (field.required && !formData[field.name]) {
        newErrors[field.name] = `${field.label} is required`;
      }
      
      if (field.validation && formData[field.name]) {
        const validationResult = field.validation(formData[field.name]);
        if (!validationResult.isValid) {
          newErrors[field.name] = validationResult.message;
        }
      }
    });
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (validateForm()) {
      onSubmit(formData);
    }
  };
  
  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {fields.map(field => (
        <div key={field.name}>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {field.label}
            {field.required && <span className="text-red-500">*</span>}
          </label>
          
          {field.type === 'text' || field.type === 'email' ? (
            <input
              type={field.type}
              value={formData[field.name] || ''}
              onChange={(e) => handleChange(field.name, e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={field.placeholder}
            />
          ) : field.type === 'textarea' ? (
            <textarea
              value={formData[field.name] || ''}
              onChange={(e) => handleChange(field.name, e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={field.rows || 3}
              placeholder={field.placeholder}
            />
          ) : field.type === 'select' ? (
            <select
              value={formData[field.name] || ''}
              onChange={(e) => handleChange(field.name, e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select {field.label}</option>
              {field.options.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          ) : null}
          
          {errors[field.name] && (
            <p className="text-red-500 text-sm mt-1">{errors[field.name]}</p>
          )}
        </div>
      ))}
      
      <button
        type="submit"
        disabled={isLoading}
        className="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded disabled:opacity-50"
      >
        {isLoading ? 'Loading...' : submitText}
      </button>
    </form>
  );
}

export default Form;
```

## Backend API Development

### 1. Creating New Endpoints

#### Step 1: Define Route Handler
```python
# In server.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

# Request/Response models
class NewFeatureRequest(BaseModel):
    user_id: str
    feature_data: dict
    options: Optional[dict] = None

class NewFeatureResponse(BaseModel):
    id: str
    name: str
    description: str
    created_at: str
    user_id: str

class NewFeatureListResponse(BaseModel):
    data: List[NewFeatureResponse]
    total_count: int
    page: int
    per_page: int

# Route handlers
@api_router.post("/new-feature/create", response_model=NewFeatureResponse)
async def create_new_feature(request: NewFeatureRequest):
    """
    Create a new feature item for the user.
    """
    try:
        logger.info(f"Creating new feature for user: {request.user_id}")
        
        # Validate user exists
        user = await users_collection.find_one({"id": request.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Process feature data
        feature_data = {
            "id": str(uuid.uuid4()),
            "user_id": request.user_id,
            "name": request.feature_data.get("name", "Untitled"),
            "description": request.feature_data.get("description", ""),
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Save to database
        result = await new_feature_collection.insert_one(feature_data)
        
        if not result.inserted_id:
            raise HTTPException(status_code=500, detail="Failed to create feature")
        
        logger.info(f"New feature created successfully: {feature_data['id']}")
        
        return NewFeatureResponse(**feature_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating new feature: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.get("/new-feature/{user_id}", response_model=NewFeatureListResponse)
async def get_user_features(user_id: str, page: int = 1, per_page: int = 20):
    """
    Get all features for a specific user.
    """
    try:
        logger.info(f"Fetching features for user: {user_id}")
        
        # Calculate pagination
        skip = (page - 1) * per_page
        
        # Get features with pagination
        cursor = new_feature_collection.find(
            {"user_id": user_id, "status": {"$ne": "deleted"}}
        ).sort("created_at", -1).skip(skip).limit(per_page)
        
        features = await cursor.to_list(per_page)
        
        # Get total count
        total_count = await new_feature_collection.count_documents(
            {"user_id": user_id, "status": {"$ne": "deleted"}}
        )
        
        # Convert to response format
        feature_responses = [
            NewFeatureResponse(**mongo_to_dict(feature)) for feature in features
        ]
        
        return NewFeatureListResponse(
            data=feature_responses,
            total_count=total_count,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error fetching user features: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.delete("/new-feature/{feature_id}")
async def delete_feature(feature_id: str, user_id: str):
    """
    Delete a feature item.
    """
    try:
        logger.info(f"Deleting feature: {feature_id} for user: {user_id}")
        
        # Find and verify ownership
        feature = await new_feature_collection.find_one({
            "id": feature_id,
            "user_id": user_id
        })
        
        if not feature:
            raise HTTPException(status_code=404, detail="Feature not found")
        
        # Soft delete (mark as deleted)
        result = await new_feature_collection.update_one(
            {"id": feature_id},
            {
                "$set": {
                    "status": "deleted",
                    "deleted_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to delete feature")
        
        logger.info(f"Feature deleted successfully: {feature_id}")
        
        return {"success": True, "message": "Feature deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting feature: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.post("/new-feature/action")
async def perform_feature_action(request: dict):
    """
    Perform a specific action on a feature.
    """
    try:
        user_id = request.get("user_id")
        item_id = request.get("item_id")
        action_type = request.get("action_type", "default")
        
        logger.info(f"Performing action {action_type} on item {item_id} for user {user_id}")
        
        # Validate feature exists and user owns it
        feature = await new_feature_collection.find_one({
            "id": item_id,
            "user_id": user_id
        })
        
        if not feature:
            raise HTTPException(status_code=404, detail="Feature not found")
        
        # Perform action based on type
        if action_type == "activate":
            update_data = {"status": "active"}
        elif action_type == "deactivate":
            update_data = {"status": "inactive"}
        else:
            # Default action
            update_data = {"last_action": datetime.utcnow().isoformat()}
        
        # Update feature
        result = await new_feature_collection.update_one(
            {"id": item_id},
            {
                "$set": {
                    **update_data,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to perform action")
        
        logger.info(f"Action {action_type} completed successfully")
        
        return {"success": True, "message": f"Action {action_type} completed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing action: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

#### Step 2: Database Collection Setup
```python
# Add to database initialization
new_feature_collection = db.new_features

# Create indexes for better performance
async def create_new_feature_indexes():
    """Create database indexes for new feature collection."""
    await new_feature_collection.create_index([("user_id", 1), ("created_at", -1)])
    await new_feature_collection.create_index([("id", 1)], unique=True)
    await new_feature_collection.create_index([("status", 1)])

# Add to startup event
@app.on_event("startup")
async def startup_event():
    # ... existing startup code
    await create_new_feature_indexes()
```

### 2. Adding External Service Integration

#### Step 1: Service Client Class
```python
# external_services/new_service_client.py
import httpx
import logging
from typing import Optional, Dict, Any
import asyncio

logger = logging.getLogger(__name__)

class NewServiceClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def make_request(
        self, 
        endpoint: str, 
        method: str = "GET", 
        data: Optional[Dict] = None,
        retries: int = 3
    ) -> Dict[Any, Any]:
        """Make request to external service with retries."""
        
        for attempt in range(retries):
            try:
                url = f"{self.base_url}{endpoint}"
                
                response = await self.client.request(
                    method=method,
                    url=url,
                    json=data
                )
                
                if response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error on attempt {attempt + 1}: {e}")
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
        
        raise Exception("All retry attempts failed")
    
    async def get_service_data(self, query: str) -> Dict[Any, Any]:
        """Get data from external service."""
        return await self.make_request(
            "/api/data",
            method="POST",
            data={"query": query}
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

# Service instance
new_service_client = None

def get_new_service_client() -> Optional[NewServiceClient]:
    """Get configured service client."""
    global new_service_client
    
    if new_service_client is None:
        api_key = os.environ.get('NEW_SERVICE_API_KEY')
        base_url = os.environ.get('NEW_SERVICE_BASE_URL', 'https://api.newservice.com')
        
        if api_key and api_key != 'your_api_key_here':
            new_service_client = NewServiceClient(api_key, base_url)
        else:
            logger.warning("New service API key not configured")
    
    return new_service_client
```

#### Step 2: Integration in Route Handler
```python
@api_router.post("/new-feature/external-data")
async def get_external_data(request: dict):
    """Get data from external service."""
    try:
        query = request.get("query", "")
        
        # Get service client
        service_client = get_new_service_client()
        
        if not service_client:
            # Fallback to mock data
            logger.warning("External service not available, using mock data")
            return {
                "data": {"mock": True, "message": "Service unavailable"},
                "source": "mock"
            }
        
        # Get data from external service
        result = await service_client.get_service_data(query)
        
        return {
            "data": result,
            "source": "external"
        }
        
    except Exception as e:
        logger.error(f"Error getting external data: {e}")
        
        # Graceful fallback
        return {
            "data": {"error": str(e), "mock": True},
            "source": "error_fallback"
        }
```

## Database Schema Updates

### 1. Adding New Collections

#### MongoDB Schema Example
```javascript
// New collection schema documentation
{
  // Collection: new_features
  "_id": ObjectId,
  "id": "uuid-string", // Unique identifier
  "user_id": "user-uuid", // Reference to users collection
  "name": "Feature Name",
  "description": "Feature description",
  "type": "feature_type", // Enumerated type
  "status": "active|inactive|deleted",
  "metadata": {
    "category": "category_name",
    "tags": ["tag1", "tag2"],
    "settings": {
      "option1": "value1",
      "option2": true
    }
  },
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-01T12:00:00Z",
  "deleted_at": null // For soft deletes
}

// Indexes
db.new_features.createIndex({ "id": 1 }, { unique: true })
db.new_features.createIndex({ "user_id": 1, "created_at": -1 })
db.new_features.createIndex({ "status": 1 })
db.new_features.createIndex({ "type": 1, "status": 1 })
```

### 2. Schema Migration Script
```python
# migrations/add_new_feature_collection.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging

logger = logging.getLogger(__name__)

async def migrate_add_new_feature_collection():
    """Migration to add new_features collection with proper indexes."""
    
    # Connect to database
    mongo_url = os.environ.get('MONGO_URL')
    client = AsyncIOMotorClient(mongo_url)
    db = client.buildyoursmartcart
    
    try:
        # Create collection if it doesn't exist
        if "new_features" not in await db.list_collection_names():
            await db.create_collection("new_features")
            logger.info("Created new_features collection")
        
        # Create indexes
        collection = db.new_features
        
        indexes = [
            {"keys": [("id", 1)], "options": {"unique": True}},
            {"keys": [("user_id", 1), ("created_at", -1)], "options": {}},
            {"keys": [("status", 1)], "options": {}},
            {"keys": [("type", 1), ("status", 1)], "options": {}}
        ]
        
        for index in indexes:
            try:
                await collection.create_index(index["keys"], **index["options"])
                logger.info(f"Created index: {index['keys']}")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info(f"Index already exists: {index['keys']}")
                else:
                    raise
        
        logger.info("New features collection migration completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(migrate_add_new_feature_collection())
```

## Third-Party Service Integration

### 1. Using Integration Playbook Expert
For external API integrations, always use the integration playbook expert:

```python
# Example: Adding a new AI service integration
"""
Call integration_playbook_expert_v2 with:

INTEGRATION: Anthropic Claude API
CONSTRAINTS: 
- Must work with existing OpenAI fallback system
- Rate limiting required
- Error handling for service unavailability
"""
```

### 2. Environment Configuration
```python
# Add to .env file
NEW_SERVICE_API_KEY=your_api_key_here
NEW_SERVICE_BASE_URL=https://api.newservice.com
NEW_SERVICE_TIMEOUT=30
NEW_SERVICE_MAX_RETRIES=3

# Add to environment validation
def validate_environment():
    """Validate required environment variables."""
    required_vars = [
        'MONGO_URL',
        'OPENAI_API_KEY',
        # ... existing vars
        'NEW_SERVICE_API_KEY'  # Add new required vars
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        raise ValueError(f"Missing environment variables: {missing_vars}")
```

## Testing New Features

### 1. Unit Tests
```javascript
// Frontend component test
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import NewFeatureScreen from '../NewFeatureScreen';

describe('NewFeatureScreen', () => {
  const mockProps = {
    user: { id: 'test-user' },
    onBack: jest.fn(),
    showNotification: jest.fn()
  };

  beforeEach(() => {
    global.fetch = jest.fn();
    jest.clearAllMocks();
  });

  test('loads and displays feature data', async () => {
    const mockData = [
      { id: '1', title: 'Test Feature', description: 'Test description' }
    ];

    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ data: mockData })
    });

    render(<NewFeatureScreen {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Test Feature')).toBeInTheDocument();
    });
  });

  test('handles actions correctly', async () => {
    // Test action functionality
    const mockData = [
      { id: '1', title: 'Test Feature', description: 'Test description' }
    ];

    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ data: mockData })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true })
      });

    render(<NewFeatureScreen {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Test Feature')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Action'));

    await waitFor(() => {
      expect(mockProps.showNotification).toHaveBeenCalledWith(
        'Action completed successfully', 
        'success'
      );
    });
  });
});
```

### 2. Backend API Tests
```python
# test_new_feature_api.py
import pytest
from httpx import AsyncClient
from server import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def mock_user():
    return {"id": "test-user-id", "email": "test@example.com"}

class TestNewFeatureAPI:
    async def test_create_feature(self, client, mock_user):
        response = await client.post(
            "/api/new-feature/create",
            json={
                "user_id": mock_user["id"],
                "feature_data": {
                    "name": "Test Feature",
                    "description": "Test description"
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Feature"
        assert data["user_id"] == mock_user["id"]

    async def test_get_user_features(self, client, mock_user):
        # Pre-create some test data
        await create_test_feature(mock_user["id"])
        
        response = await client.get(f"/api/new-feature/{mock_user['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0

    async def test_delete_feature(self, client, mock_user):
        # Create feature first
        feature_id = await create_test_feature(mock_user["id"])
        
        response = await client.delete(
            f"/api/new-feature/{feature_id}",
            params={"user_id": mock_user["id"]}
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
```

### 3. Integration Tests
```javascript
// e2e/new-feature-flow.spec.js
import { test, expect } from '@playwright/test';

test.describe('New Feature Integration', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/');
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForSelector('[data-testid="dashboard"]');
  });

  test('complete new feature workflow', async ({ page }) => {
    // Navigate to new feature
    await page.click('button:has-text("New Feature")');
    await page.waitForSelector('[data-testid="new-feature-screen"]');

    // Verify feature list loads
    await expect(page.locator('.feature-card').first()).toBeVisible();

    // Test feature action
    await page.click('.feature-card button:has-text("Action")');
    
    // Verify success notification
    await expect(page.locator('text=Action completed successfully')).toBeVisible();

    // Test navigation back
    await page.click('button:has-text("Back to Dashboard")');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
  });

  test('handles feature errors gracefully', async ({ page }) => {
    // Mock API failure
    await page.route('/api/new-feature/*', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Service unavailable' })
      });
    });

    await page.click('button:has-text("New Feature")');
    
    // Should show error state
    await expect(page.locator('text=Error Loading Feature')).toBeVisible();
    
    // Should allow retry
    await expect(page.locator('button:has-text("Retry")')).toBeVisible();
  });
});
```

## Deployment Considerations

### 1. Environment Variables
```bash
# Add to deployment scripts
# Production environment variables
export NEW_SERVICE_API_KEY="prod_api_key"
export NEW_SERVICE_BASE_URL="https://api.newservice.com"
export NEW_SERVICE_TIMEOUT=30

# Staging environment variables
export NEW_SERVICE_API_KEY="staging_api_key"
export NEW_SERVICE_BASE_URL="https://staging-api.newservice.com"
```

### 2. Database Migrations
```bash
# Run migrations before deployment
python migrations/add_new_feature_collection.py

# Verify migration
python -c "
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def verify():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client.buildyoursmartcart
    collections = await db.list_collection_names()
    assert 'new_features' in collections
    print('Migration verified successfully')
    client.close()

asyncio.run(verify())
"
```

### 3. Feature Flags
```python
# Add feature flag support
FEATURE_FLAGS = {
    "new_feature_enabled": os.environ.get("ENABLE_NEW_FEATURE", "false").lower() == "true",
    "new_feature_beta": os.environ.get("NEW_FEATURE_BETA", "false").lower() == "true"
}

def is_feature_enabled(feature_name: str, user_id: str = None) -> bool:
    """Check if feature is enabled for user."""
    if not FEATURE_FLAGS.get(feature_name, False):
        return False
    
    # Beta feature logic
    if feature_name.endswith("_beta") and user_id:
        # Enable for specific beta users
        beta_users = os.environ.get("BETA_USERS", "").split(",")
        return user_id in beta_users
    
    return True

# Use in route handlers
@api_router.get("/new-feature/{user_id}")
async def get_user_features(user_id: str):
    if not is_feature_enabled("new_feature_enabled", user_id):
        raise HTTPException(status_code=404, detail="Feature not available")
    
    # Feature implementation
    ...
```

## Common Integration Patterns

### 1. Data Transformation Pattern
```python
# Transform external API data to internal format
def transform_external_data(external_data: Dict) -> Dict:
    """Transform external API response to internal format."""
    return {
        "id": external_data.get("external_id"),
        "name": external_data.get("title", "Untitled"),
        "description": external_data.get("desc", ""),
        "type": "external",
        "metadata": {
            "external_source": True,
            "original_data": external_data
        },
        "created_at": datetime.utcnow().isoformat()
    }
```

### 2. Fallback Pattern
```python
# Graceful fallback when external service fails
async def get_data_with_fallback(query: str):
    """Get data with fallback to local/cache."""
    try:
        # Try external service first
        external_client = get_external_service_client()
        if external_client:
            return await external_client.get_data(query)
    except Exception as e:
        logger.warning(f"External service failed: {e}, using fallback")
    
    # Fallback to cached/local data
    return await get_cached_data(query) or get_mock_data(query)
```

### 3. Event-Driven Pattern
```python
# Event system for feature interactions
from typing import Callable, List
from dataclasses import dataclass

@dataclass
class FeatureEvent:
    event_type: str
    user_id: str
    feature_id: str
    data: Dict

class EventBus:
    def __init__(self):
        self.handlers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, handler: Callable):
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    async def publish(self, event: FeatureEvent):
        if event.event_type in self.handlers:
            for handler in self.handlers[event.event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Event handler failed: {e}")

# Usage
event_bus = EventBus()

# Subscribe to events
@event_bus.subscribe("feature_created")
async def handle_feature_created(event: FeatureEvent):
    # Send notification, update analytics, etc.
    logger.info(f"Feature created: {event.feature_id} by {event.user_id}")

# Publish events in route handlers
@api_router.post("/new-feature/create")
async def create_new_feature(request: NewFeatureRequest):
    # ... create feature logic
    
    # Publish event
    await event_bus.publish(FeatureEvent(
        event_type="feature_created",
        user_id=request.user_id,
        feature_id=feature_data["id"],
        data=feature_data
    ))
    
    return feature_data
```

### 4. Caching Pattern
```python
from functools import wraps
import asyncio

# Simple in-memory cache with TTL
class SimpleCache:
    def __init__(self):
        self.cache = {}
        self.expiry = {}
    
    def set(self, key: str, value: any, ttl: int = 300):
        self.cache[key] = value
        self.expiry[key] = time.time() + ttl
    
    def get(self, key: str):
        if key in self.cache:
            if time.time() < self.expiry[key]:
                return self.cache[key]
            else:
                del self.cache[key]
                del self.expiry[key]
        return None

cache = SimpleCache()

def cached(ttl: int = 300):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator

# Usage
@cached(ttl=600)  # Cache for 10 minutes
async def get_external_data(query: str):
    return await external_service.get_data(query)
```

## Documentation Standards

### 1. Code Documentation
```python
def new_feature_function(param1: str, param2: Optional[int] = None) -> Dict:
    """
    Brief description of the function.
    
    Detailed description explaining what the function does,
    any side effects, and important usage notes.
    
    Args:
        param1: Description of param1
        param2: Optional parameter description
    
    Returns:
        Dictionary containing the result data
    
    Raises:
        ValueError: When param1 is invalid
        HTTPException: When external service fails
    
    Examples:
        >>> result = new_feature_function("test", 123)
        >>> print(result["status"])
        "success"
    """
    pass
```

### 2. API Documentation
Update the API reference documentation with new endpoints:

```markdown
### New Feature Endpoints

#### Create Feature
Creates a new feature item for the user.

```http
POST /api/new-feature/create
Content-Type: application/json

{
  "user_id": "uuid-string",
  "feature_data": {
    "name": "Feature Name",
    "description": "Feature description"
  }
}
```

**Response (200 OK):**
```json
{
  "id": "feature-uuid",
  "name": "Feature Name",
  "description": "Feature description",
  "created_at": "2025-01-01T12:00:00Z",
  "user_id": "user-uuid"
}
```
```

## Monitoring and Analytics

### 1. Add Logging
```python
import logging
from datetime import datetime

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Add feature-specific logging
@api_router.post("/new-feature/create")
async def create_new_feature(request: NewFeatureRequest):
    start_time = datetime.utcnow()
    
    try:
        # Log request
        logger.info(
            "Creating new feature",
            extra={
                "user_id": request.user_id,
                "feature_type": request.feature_data.get("type"),
                "timestamp": start_time.isoformat()
            }
        )
        
        # Implementation...
        result = await create_feature_logic(request)
        
        # Log success
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            "Feature created successfully",
            extra={
                "user_id": request.user_id,
                "feature_id": result["id"],
                "duration_seconds": duration,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return result
        
    except Exception as e:
        # Log error
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.error(
            "Feature creation failed",
            extra={
                "user_id": request.user_id,
                "error": str(e),
                "duration_seconds": duration,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        raise
```

### 2. Add Metrics
```python
from collections import defaultdict
import time

# Simple metrics collection
class Metrics:
    def __init__(self):
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
    
    def increment(self, metric_name: str, value: int = 1):
        self.counters[metric_name] += value
    
    def record_time(self, metric_name: str, duration: float):
        self.timers[metric_name].append(duration)
    
    def get_stats(self) -> Dict:
        stats = {
            "counters": dict(self.counters),
            "timers": {}
        }
        
        for metric, times in self.timers.items():
            if times:
                stats["timers"][metric] = {
                    "count": len(times),
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times)
                }
        
        return stats

metrics = Metrics()

# Usage in route handlers
@api_router.post("/new-feature/create")
async def create_new_feature(request: NewFeatureRequest):
    start_time = time.time()
    
    try:
        metrics.increment("new_feature.create.attempts")
        
        result = await create_feature_logic(request)
        
        metrics.increment("new_feature.create.success")
        metrics.record_time("new_feature.create.duration", time.time() - start_time)
        
        return result
        
    except Exception as e:
        metrics.increment("new_feature.create.errors")
        raise

# Metrics endpoint
@api_router.get("/metrics/new-feature")
async def get_new_feature_metrics():
    return metrics.get_stats()
```

This comprehensive guide provides all the necessary patterns and examples for integrating new features into the AI Chef application while maintaining code quality, performance, and reliability standards.

---

**Last Updated**: January 2025
**Guide Version**: 2.0.0