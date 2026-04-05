# Assistant Availability API for Handlers

This document describes the API endpoints that allow handlers and admins to view and manage assistant availability status (online/offline).

## Overview

Handlers can now:
- View all assistants with their online/offline status
- Filter assistants by availability status (online/offline)
- Get statistics about assistant availability
- Combine availability filters with verification status and role filters

## API Endpoints

### 1. Assistant List with Availability (`/accounts/user/list/`)

**Method:** GET  
**Permission:** Handler or Admin  
**Description:** List all assistants with detailed information including online/offline status

#### Query Parameters:
- `is_online` - Filter by availability status (`true`/`false`)
- `verification_status` - Filter by verification status (`verified`, `pending`, `rejected`, `not_submitted`)
- `user_role` - Filter by role (`rider`, `service_provider`)
- `service_type` - Filter by service type (for service providers)
- `search` - Search by username, name, email, or phone
- `ordering` - Order by fields (`date_joined`, `first_name`, `last_name`, `is_online`)

#### Examples:
```bash
# Get all online assistants
GET /accounts/user/list/?is_online=true

# Get offline verified assistants
GET /accounts/user/list/?is_online=false&verification_status=verified

# Get online riders
GET /accounts/user/list/?is_online=true&user_role=rider

# Order by online status (online first)
GET /accounts/user/list/?ordering=-is_online
```

#### Response:
```json
[
  {
    "id": 1,
    "username": "assistant1",
    "email": "assistant1@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "user_type": "assistant",
    "phone_number": "+1234567890",
    "is_verified": true,
    "email_verified": true,
    "is_online": true,
    "date_joined": "2024-01-15T10:30:00Z",
    "verification_status": "verified",
    "user_role": "rider",
    "service_type": null,
    "full_name_from_verification": "John Doe",
    "area_of_operation": "Downtown",
    "years_of_experience": "more_than_a_year"
  }
]
```

### 2. Assistant Availability List (`/accounts/assistants/availability/`)

**Method:** GET  
**Permission:** Handler or Admin  
**Description:** Specialized endpoint for viewing assistant availability with summary statistics

#### Query Parameters:
- `status` - Filter by availability (`online`, `offline`, or omit for all)
- `verification_status` - Filter by verification status
- `user_role` - Filter by role

#### Examples:
```bash
# Get all online assistants with summary
GET /accounts/assistants/availability/?status=online

# Get offline verified assistants
GET /accounts/assistants/availability/?status=offline&verification_status=verified
```

#### Response:
```json
{
  "summary": {
    "total": 15,
    "online": 8,
    "offline": 7
  },
  "assistants": [
    {
      "id": 1,
      "username": "assistant1",
      "is_online": true,
      // ... other assistant details
    }
  ]
}
```

### 3. Assistant Statistics (`/accounts/assistants/stats/`)

**Method:** GET  
**Permission:** Handler or Admin  
**Description:** Get comprehensive statistics about assistants including availability status

#### Response:
```json
{
  "total_assistants": 25,
  "verification_status": {
    "verified": 15,
    "pending": 5,
    "rejected": 2,
    "not_submitted": 3
  },
  "availability_status": {
    "online": 12,
    "offline": 13
  },
  "roles": {
    "riders": 18,
    "service_providers": 7,
    "unspecified": 0
  },
  "service_types": [
    {
      "service": "Plumbing",
      "count": 3
    },
    {
      "service": "Cleaning",
      "count": 2
    }
  ]
}
```

## Usage Examples

### Frontend Implementation

```javascript
// Get all online assistants
const getOnlineAssistants = async () => {
  const response = await fetch('/accounts/user/list/?is_online=true', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};

// Get availability summary
const getAvailabilitySummary = async () => {
  const response = await fetch('/accounts/assistants/availability/', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};

// Get statistics including availability
const getAssistantStats = async () => {
  const response = await fetch('/accounts/assistants/stats/', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};
```

### Dashboard Implementation

```javascript
// Dashboard component for handlers
const AssistantDashboard = () => {
  const [stats, setStats] = useState(null);
  const [onlineAssistants, setOnlineAssistants] = useState([]);
  const [offlineAssistants, setOfflineAssistants] = useState([]);

  useEffect(() => {
    // Load statistics
    getAssistantStats().then(setStats);
    
    // Load online assistants
    getOnlineAssistants().then(setOnlineAssistants);
    
    // Load offline assistants
    fetch('/accounts/user/list/?is_online=false')
      .then(res => res.json())
      .then(setOfflineAssistants);
  }, []);

  return (
    <div>
      <h2>Assistant Availability Dashboard</h2>
      
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Total Assistants</h3>
            <p>{stats.total_assistants}</p>
          </div>
          <div className="stat-card online">
            <h3>Online</h3>
            <p>{stats.availability_status.online}</p>
          </div>
          <div className="stat-card offline">
            <h3>Offline</h3>
            <p>{stats.availability_status.offline}</p>
          </div>
        </div>
      )}
      
      <div className="assistant-lists">
        <div className="online-list">
          <h3>Online Assistants ({onlineAssistants.length})</h3>
          {onlineAssistants.map(assistant => (
            <AssistantCard key={assistant.id} assistant={assistant} />
          ))}
        </div>
        
        <div className="offline-list">
          <h3>Offline Assistants ({offlineAssistants.length})</h3>
          {offlineAssistants.map(assistant => (
            <AssistantCard key={assistant.id} assistant={assistant} />
          ))}
        </div>
      </div>
    </div>
  );
};
```

## Permissions

- **Handlers** (`user_type='handler'`) have full access to all endpoints
- **Admins** (`user_type='admin'`) have full access to all endpoints
- **Assistants** and **Users** cannot access these endpoints

## Notes

1. The `is_online` field is automatically managed by assistants through the `/accounts/assistant/availability/` endpoint
2. Handlers can only view availability status, not modify it
3. All endpoints support pagination for large datasets
4. The availability status is real-time based on when assistants last updated their status
5. Filtering can be combined (e.g., online + verified + riders)

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200 OK` - Success
- `403 Forbidden` - Insufficient permissions
- `500 Internal Server Error` - Server error

Error responses include descriptive messages:
```json
{
  "error": "Failed to fetch assistant availability",
  "details": "Database connection error"
}
```