# Component Integration Patterns & Guidelines

## Overview
This document provides comprehensive patterns and guidelines for integrating new components, features, and screens into the AI Recipe + Grocery Delivery App architecture.

## Component Architecture Patterns

### Base Component Pattern
```javascript
// Template for creating new components
import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';

const NewComponentScreen = ({ 
  user, 
  onBack, 
  showNotification, 
  ...additionalProps 
}) => {
  // State management
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Data fetching effect
  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/endpoint`);
        if (!response.ok) throw new Error('Failed to load data');
        
        const data = await response.json();
        setData(data);
        
      } catch (error) {
        setError(error.message);
        showNotification('Failed to load data', 'error');
      } finally {
        setIsLoading(false);
      }
    };

    if (user?.id) {
      loadData();
    }
  }, [user?.id, showNotification]);

  // Event handlers
  const handleAction = useCallback(async (actionData) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(actionData)
      });

      if (!response.ok) throw new Error('Action failed');

      showNotification('Action completed successfully', 'success');
    } catch (error) {
      showNotification('Action failed', 'error');
    }
  }, [showNotification]);

  // Render loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg p-8 text-center max-w-md">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-red-600 mb-4">Error</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button onClick={onBack} className="btn-primary">
            Go Back
          </button>
        </div>
      </div>
    );
  }

  // Main render
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      {/* Header */}
      <div className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={onBack}
                className="text-blue-600 hover:text-blue-700 font-semibold flex items-center"
              >
                ← Back
              </button>
              <h1 className="text-2xl font-bold text-gray-800">
                Component Title
              </h1>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Component content */}
      </div>
    </div>
  );
};

// PropTypes for development
NewComponentScreen.propTypes = {
  user: PropTypes.shape({
    id: PropTypes.string.required,
    email: PropTypes.string.required
  }).required,
  onBack: PropTypes.func.required,
  showNotification: PropTypes.func.required
};

export default NewComponentScreen;
```

### Data Management Pattern
```javascript
// Custom hook for data management
import { useState, useEffect, useCallback } from 'react';

export const useDataManager = (apiEndpoint, user, dependencies = []) => {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api${apiEndpoint}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const result = await response.json();
      setData(result);

    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [apiEndpoint, ...dependencies]);

  useEffect(() => {
    if (user?.id) {
      loadData();
    }
  }, [user?.id, loadData]);

  const refetch = useCallback(() => {
    loadData();
  }, [loadData]);

  const updateData = useCallback((newData) => {
    setData(newData);
  }, []);

  return { data, isLoading, error, refetch, updateData };
};

// Usage in components
const MyComponent = ({ user, showNotification }) => {
  const { 
    data: recipes, 
    isLoading, 
    error, 
    refetch,
    updateData 
  } = useDataManager('/recipes/history/${user.id}', user);

  // Component logic using the data
};
```

### Form Handling Pattern
```javascript
// Reusable form hook
import { useState, useCallback } from 'react';

export const useForm = (initialValues, validationSchema, onSubmit) => {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = useCallback((name, value) => {
    setValues(prev => ({ ...prev, [name]: value }));
    
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  }, [errors]);

  const validate = useCallback(() => {
    const newErrors = {};
    
    Object.keys(validationSchema).forEach(field => {
      const rules = validationSchema[field];
      const value = values[field];
      
      if (rules.required && (!value || value.toString().trim() === '')) {
        newErrors[field] = `${field} is required`;
      } else if (rules.minLength && value && value.length < rules.minLength) {
        newErrors[field] = `${field} must be at least ${rules.minLength} characters`;
      } else if (rules.pattern && value && !rules.pattern.test(value)) {
        newErrors[field] = rules.message || `${field} format is invalid`;
      } else if (rules.custom && value) {
        const customError = rules.custom(value);
        if (customError) newErrors[field] = customError;
      }
    });
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [values, validationSchema]);

  const handleSubmit = useCallback(async (e) => {
    if (e) e.preventDefault();
    
    if (!validate()) return;
    
    setIsSubmitting(true);
    try {
      await onSubmit(values);
    } catch (error) {
      console.error('Form submission error:', error);
    } finally {
      setIsSubmitting(false);
    }
  }, [values, validate, onSubmit]);

  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setIsSubmitting(false);
  }, [initialValues]);

  return {
    values,
    errors,
    isSubmitting,
    handleChange,
    handleSubmit,
    reset
  };
};

// Usage example
const RecipeForm = ({ onSubmit, showNotification }) => {
  const validationSchema = {
    cuisine: { required: true },
    difficulty: { required: true },
    servings: { 
      required: true,
      custom: (value) => {
        const num = parseInt(value);
        if (isNaN(num) || num < 1 || num > 20) {
          return 'Servings must be between 1 and 20';
        }
        return null;
      }
    }
  };

  const { values, errors, isSubmitting, handleChange, handleSubmit } = useForm(
    { cuisine: '', difficulty: '', servings: 4 },
    validationSchema,
    async (formData) => {
      try {
        await onSubmit(formData);
        showNotification('Recipe generation started!', 'success');
      } catch (error) {
        showNotification('Failed to start recipe generation', 'error');
      }
    }
  );

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label>Cuisine</label>
        <select 
          value={values.cuisine}
          onChange={(e) => handleChange('cuisine', e.target.value)}
        >
          <option value="">Select cuisine</option>
          <option value="italian">Italian</option>
          <option value="mexican">Mexican</option>
        </select>
        {errors.cuisine && <span className="error">{errors.cuisine}</span>}
      </div>
      
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Generating...' : 'Generate Recipe'}
      </button>
    </form>
  );
};
```

## Backend Integration Patterns

### Route Handler Pattern
```python
# Standard route handler pattern
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, validator
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/new-feature", tags=["new-feature"])

# Request/Response models
class NewFeatureRequest(BaseModel):
    user_id: str
    feature_data: Dict[str, Any]
    options: Optional[Dict] = {}
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not re.match(r'^[a-f0-9-]{36}$', v):
            raise ValueError('Invalid user ID format')
        return v

class NewFeatureResponse(BaseModel):
    id: str
    name: str
    status: str
    created_at: str
    data: Dict[str, Any]

# Dependency for user authentication
async def get_authenticated_user(user_id: str) -> dict:
    user = await users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Route handlers
@router.post("/create", response_model=NewFeatureResponse)
async def create_new_feature(
    request: NewFeatureRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(lambda: get_authenticated_user(request.user_id))
):
    """Create a new feature for the user."""
    try:
        logger.info(f"Creating new feature for user: {request.user_id}")
        
        # Process feature data
        feature_data = {
            "id": str(uuid.uuid4()),
            "user_id": request.user_id,
            "name": request.feature_data.get("name", "Untitled Feature"),
            "status": "active",
            "data": request.feature_data,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Save to database
        result = await new_features_collection.insert_one(feature_data)
        if not result.inserted_id:
            raise HTTPException(status_code=500, detail="Failed to create feature")
        
        # Add background task
        background_tasks.add_task(
            send_feature_notification, 
            user["email"], 
            feature_data["name"]
        )
        
        logger.info(f"Feature created successfully: {feature_data['id']}")
        
        return NewFeatureResponse(
            id=feature_data["id"],
            name=feature_data["name"],
            status=feature_data["status"],
            created_at=feature_data["created_at"],
            data=feature_data["data"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating feature: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/list/{user_id}", response_model=List[NewFeatureResponse])
async def list_user_features(
    user_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_authenticated_user)
):
    """Get paginated list of user features."""
    try:
        skip = (page - 1) * per_page
        
        cursor = new_features_collection.find(
            {"user_id": user_id, "status": {"$ne": "deleted"}}
        ).sort("created_at", -1).skip(skip).limit(per_page)
        
        features = await cursor.to_list(per_page)
        
        return [
            NewFeatureResponse(
                id=feature["id"],
                name=feature["name"],
                status=feature["status"],
                created_at=feature["created_at"],
                data=feature["data"]
            )
            for feature in features
        ]
        
    except Exception as e:
        logger.error(f"Error listing features: {e}")
        raise HTTPException(status_code=500, detail="Failed to list features")

# Background task
async def send_feature_notification(email: str, feature_name: str):
    """Send notification about new feature creation."""
    try:
        # Send email or push notification
        logger.info(f"Sent notification about feature '{feature_name}' to {email}")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
```

### Database Service Pattern
```python
# Database service abstraction
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorCollection

class BaseService(ABC):
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
    
    async def create(self, data: Dict[str, Any]) -> str:
        """Create a new document and return its ID."""
        data["created_at"] = datetime.utcnow().isoformat()
        result = await self.collection.insert_one(data)
        return data["id"]
    
    async def find_by_id(self, doc_id: str) -> Optional[Dict]:
        """Find document by ID."""
        return await self.collection.find_one({"id": doc_id})
    
    async def find_by_user(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Find documents by user ID."""
        cursor = self.collection.find({"user_id": user_id}).limit(limit)
        return await cursor.to_list(limit)
    
    async def update_by_id(self, doc_id: str, update_data: Dict) -> bool:
        """Update document by ID."""
        update_data["updated_at"] = datetime.utcnow().isoformat()
        result = await self.collection.update_one(
            {"id": doc_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def delete_by_id(self, doc_id: str) -> bool:
        """Soft delete document by ID."""
        result = await self.collection.update_one(
            {"id": doc_id},
            {"$set": {
                "status": "deleted",
                "deleted_at": datetime.utcnow().isoformat()
            }}
        )
        return result.modified_count > 0

class RecipeService(BaseService):
    def __init__(self, recipes_collection):
        super().__init__(recipes_collection)
    
    async def find_by_cuisine(self, user_id: str, cuisine: str) -> List[Dict]:
        """Find recipes by cuisine type."""
        cursor = self.collection.find({
            "user_id": user_id,
            "cuisine_type": cuisine.lower(),
            "status": {"$ne": "deleted"}
        })
        return await cursor.to_list(None)
    
    async def get_recipe_stats(self, user_id: str) -> Dict:
        """Get recipe statistics for user."""
        pipeline = [
            {"$match": {"user_id": user_id, "status": {"$ne": "deleted"}}},
            {"$group": {
                "_id": "$cuisine_type",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        
        stats = []
        async for doc in self.collection.aggregate(pipeline):
            stats.append(doc)
        
        return {
            "total_recipes": sum(stat["count"] for stat in stats),
            "by_cuisine": stats
        }

# Service instances
recipe_service = RecipeService(recipes_collection)
```

## UI Component Patterns

### Reusable UI Components
```javascript
// Button component with variants
import React from 'react';
import classNames from 'classnames';

const Button = ({ 
  children, 
  variant = 'primary', 
  size = 'medium', 
  disabled = false,
  loading = false,
  icon = null,
  onClick,
  className = '',
  ...props 
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-semibold rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const variants = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white focus:ring-blue-500',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800 focus:ring-gray-500',
    success: 'bg-green-600 hover:bg-green-700 text-white focus:ring-green-500',
    danger: 'bg-red-600 hover:bg-red-700 text-white focus:ring-red-500',
    outline: 'border-2 border-blue-600 text-blue-600 hover:bg-blue-50 focus:ring-blue-500'
  };
  
  const sizes = {
    small: 'px-3 py-1.5 text-sm',
    medium: 'px-4 py-2 text-base',
    large: 'px-6 py-3 text-lg'
  };
  
  const buttonClasses = classNames(
    baseClasses,
    variants[variant],
    sizes[size],
    {
      'opacity-50 cursor-not-allowed': disabled || loading,
      'cursor-wait': loading
    },
    className
  );
  
  return (
    <button
      className={buttonClasses}
      disabled={disabled || loading}
      onClick={onClick}
      {...props}
    >
      {loading && (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
      )}
      {icon && !loading && <span className="mr-2">{icon}</span>}
      {children}
    </button>
  );
};

// Card component
const Card = ({ 
  children, 
  title = null, 
  actions = null, 
  className = '', 
  hoverable = false 
}) => {
  const cardClasses = classNames(
    'bg-white rounded-xl shadow-lg overflow-hidden',
    {
      'hover:shadow-xl transform hover:scale-105 transition-all duration-200 cursor-pointer': hoverable
    },
    className
  );
  
  return (
    <div className={cardClasses}>
      {title && (
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
          {actions && <div className="flex space-x-2">{actions}</div>}
        </div>
      )}
      <div className="p-6">
        {children}
      </div>
    </div>
  );
};

// Loading spinner
const LoadingSpinner = ({ size = 'medium', message = null }) => {
  const sizes = {
    small: 'h-4 w-4',
    medium: 'h-8 w-8',
    large: 'h-12 w-12'
  };
  
  return (
    <div className="flex flex-col items-center justify-center p-8">
      <div className={`${sizes[size]} border-4 border-blue-500 border-t-transparent rounded-full animate-spin`} />
      {message && <p className="mt-4 text-gray-600">{message}</p>}
    </div>
  );
};

// Export all components
export { Button, Card, LoadingSpinner };
```

### Modal Pattern
```javascript
// Modal component with overlay
import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';

const Modal = ({ 
  isOpen, 
  onClose, 
  title, 
  children, 
  size = 'medium',
  showCloseButton = true 
}) => {
  // Close on escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);
  
  if (!isOpen) return null;
  
  const sizes = {
    small: 'max-w-md',
    medium: 'max-w-lg',
    large: 'max-w-2xl',
    full: 'max-w-6xl'
  };
  
  const modalContent = (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className={`relative bg-white rounded-xl shadow-2xl ${sizes[size]} w-full max-h-screen overflow-y-auto`}>
        {/* Header */}
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between p-6 border-b">
            <h2 className="text-xl font-semibold">{title}</h2>
            {showCloseButton && (
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 text-2xl"
              >
                ×
              </button>
            )}
          </div>
        )}
        
        {/* Content */}
        <div className="p-6">
          {children}
        </div>
      </div>
    </div>
  );
  
  return createPortal(modalContent, document.body);
};

// Usage example
const ExampleModal = ({ isOpen, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({ name: '', description: '' });
  
  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
    onClose();
  };
  
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create New Item"
      size="medium"
    >
      <form onSubmit={handleSubmit}>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Name
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({...prev, name: e.target.value}))}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
          </div>
          
          <div className="flex justify-end space-x-3 pt-4">
            <Button variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Create
            </Button>
          </div>
        </div>
      </form>
    </Modal>
  );
};
```

## Testing Integration Patterns

### Component Testing Pattern
```javascript
// Testing utilities and patterns
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';

// Mock factory for creating test props
export const createMockProps = (overrides = {}) => ({
  user: { id: 'test-user-id', email: 'test@example.com' },
  onBack: jest.fn(),
  showNotification: jest.fn(),
  ...overrides
});

// API response mock factory
export const createMockAPIResponse = (data, ok = true) => ({
  ok,
  json: () => Promise.resolve(data),
  status: ok ? 200 : 400,
  statusText: ok ? 'OK' : 'Bad Request'
});

// Test helper for async component testing
export const renderWithAsyncData = async (Component, props, apiResponse) => {
  // Mock fetch
  global.fetch = jest.fn().mockResolvedValue(createMockAPIResponse(apiResponse));
  
  // Render component
  render(<Component {...props} />);
  
  // Wait for data to load
  await waitFor(() => {
    expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
  });
  
  return { fetch: global.fetch };
};

// Example test using patterns
describe('NewFeatureScreen', () => {
  const defaultProps = createMockProps();
  
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  test('renders loading state initially', () => {
    render(<NewFeatureScreen {...defaultProps} />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
  
  test('loads and displays data successfully', async () => {
    const mockData = { features: [{ id: '1', name: 'Test Feature' }] };
    
    const { fetch } = await renderWithAsyncData(
      NewFeatureScreen,
      defaultProps,
      mockData
    );
    
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/new-feature')
    );
    expect(screen.getByText('Test Feature')).toBeInTheDocument();
  });
  
  test('handles API errors gracefully', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('API Error'));
    
    render(<NewFeatureScreen {...defaultProps} />);
    
    await waitFor(() => {
      expect(defaultProps.showNotification).toHaveBeenCalledWith(
        'Failed to load data',
        'error'
      );
    });
  });
});
```

This comprehensive guide provides software engineers with proven patterns and examples for effectively integrating new components and features into the AI Recipe + Grocery Delivery App architecture while maintaining consistency, quality, and maintainability.