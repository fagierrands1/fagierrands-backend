# Locations App

This app handles geospatial functionality for the Fagierrands application.

## Geospatial Implementation

The app uses a simplified approach to geospatial functionality that doesn't require GDAL:

1. **Backend**: Uses simple latitude and longitude fields in models with custom distance calculations using the Haversine formula.
2. **Frontend**: Uses JavaScript-based mapping libraries (Leaflet) directly in the React frontend.

## API Endpoints

- `GET /locations/map-config/`: Returns map configuration for the frontend
- `GET /locations/locations/`: List all user locations
- `POST /locations/locations/`: Create a new location
- `GET /locations/<id>/`: Get a specific location
- `PUT/PATCH /locations/<id>/`: Update a location
- `DELETE /locations/<id>/`: Delete a location
- `POST /locations/<id>/set-default/`: Set a location as default
- `GET /locations/current/`: Get the user's current location
- `POST /locations/current/update/`: Update the user's current location
- `GET /locations/all-users/`: Get locations of all users (admin/handler only)
- `POST /locations/calculate-distance/`: Calculate distance between two points

## Waypoints and Routes

The app also provides endpoints for managing waypoints and route calculations:

- `GET /locations/waypoints/`: List waypoints
- `POST /locations/waypoints/`: Create a waypoint
- `GET /locations/waypoints/<id>/`: Get a specific waypoint
- `PUT/PATCH /locations/waypoints/<id>/`: Update a waypoint
- `DELETE /locations/waypoints/<id>/`: Delete a waypoint
- `POST /locations/waypoints/<id>/mark-visited/`: Mark a waypoint as visited
- `GET /locations/waypoints/for-order/?order_id=<id>`: Get waypoints for a specific order

- `GET /locations/routes/`: List routes
- `POST /locations/routes/`: Create a route
- `GET /locations/routes/<id>/`: Get a specific route
- `PUT/PATCH /locations/routes/<id>/`: Update a route
- `DELETE /locations/routes/<id>/`: Delete a route
- `GET /locations/routes/for-order/?order_id=<id>`: Get routes for a specific order

## JavaScript Utilities

The app provides JavaScript utilities for geospatial calculations in `static/js/geo_utils.js`:

- `calculateDistance(lat1, lon1, lat2, lon2)`: Calculate distance between two points
- `calculateBearing(lat1, lon1, lat2, lon2)`: Calculate bearing between two points
- `calculateMidpoint(lat1, lon1, lat2, lon2)`: Calculate midpoint between two points
- `isPointWithinRadius(lat1, lon1, lat2, lon2, radiusKm)`: Check if a point is within a radius