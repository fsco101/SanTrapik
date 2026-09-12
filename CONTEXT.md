# SanTrapik

## Project Context

**SanTrapik** is an AI-powered, web-based traffic intelligence and road incident monitoring system designed specifically for the **Philippines**, with an initial focus on **Metro Manila**.

SanTrapik is intended to provide users with an immediate and understandable view of the traffic situation along a selected route. Unlike general-purpose navigation applications, the primary purpose of SanTrapik is **traffic intelligence**: determining the severity of congestion, identifying incidents affecting a route, showing when an incident was reported, estimating the resulting delay, and predicting when congestion is likely to improve.

SanTrapik is an **open-access system**. The current version does not require users to create an account or log in.

---

# System Vision

SanTrapik aims to answer four primary questions:

1. **Where is the congestion?**
2. **How severe is the congestion?**
3. **What is causing the congestion?**
4. **When is the congestion expected to improve?**

The system should provide a clear, data-driven view of Philippine road conditions, beginning with Metro Manila.

The system should focus on helping users **understand the current traffic situation**, rather than attempting to completely replace existing navigation applications.

---

# Core Objective

The primary objective of SanTrapik is to develop a web-based traffic intelligence platform that analyzes a user's selected route and provides:

- Current traffic conditions
- Congestion severity
- Active road incidents
- Incident timestamps
- Estimated travel delay
- Historical traffic information
- Traffic trends
- Alternative route information
- AI/ML-based congestion prediction
- Estimated congestion relief time

The central feature of the system is:

> **Route-specific congestion intelligence with predicted congestion relief time.**

---

# Target Users

SanTrapik is designed for:

- Daily commuters
- Private vehicle drivers
- Motorcycle riders
- Public transportation users
- Delivery riders and drivers
- Fleet operators
- Students and employees commuting within Metro Manila
- Individuals planning trips during high-traffic periods
- Traffic and transportation researchers

The system should be accessible to the general public without requiring registration.

---

# User Access Model

The current version of SanTrapik will **not require login or signup**.

Users should be able to open the website and immediately use its main traffic-monitoring functionality.

The public interface should not require:

- User accounts
- Passwords
- JWT authentication
- Firebase Authentication
- OAuth
- User profiles
- Personal account information

The system should therefore prioritize **anonymous public access**.

An administrative interface may be introduced in a future version if necessary for managing traffic data, incidents, road information, or machine-learning models. However, an admin system is not part of the initial public-facing scope unless specifically required.

---

# Main User Flow

The basic user experience should follow this process:

```text
User opens SanTrapik
        ↓
User enters starting point
        ↓
User enters destination
        ↓
System generates or retrieves route
        ↓
System divides/analyzes route road segments
        ↓
System retrieves available traffic information
        ↓
System identifies incidents affecting the route
        ↓
System calculates estimated delay
        ↓
AI/ML analyzes current and historical conditions
        ↓
System predicts congestion relief
        ↓
User receives traffic intelligence report
```

---

# Route Input

The system shall allow users to provide:

```text
START POINT
[ Quezon City ]

DESTINATION
[ Makati ]

[ ANALYZE ROUTE ]
```

The system should then retrieve or generate a suitable route between the selected locations.

---

# Route Analysis

SanTrapik should analyze the individual road segments that make up the selected route.

Example:

```text
START
  ↓
Commonwealth Avenue
  [HEAVY] Heavy Traffic
  ↓
Quezon Avenue
  [SEVERE] Severe Traffic
  ↓
EDSA
  [SEVERE] Severe Traffic + Accident
  ↓
Ortigas
  [MODERATE] Moderate Traffic
  ↓
Makati
  [NORMAL] Normal Traffic
  ↓
DESTINATION
```

Whenever data is available, each road segment should contain:

- Road name
- Traffic condition
- Average speed
- Congestion severity
- Congestion percentage, if available
- Incident status
- Incident type
- Incident timestamp
- Estimated delay
- Predicted congestion relief time
- Historical traffic information
- Data source
- Last updated timestamp

---

# Traffic Classification

SanTrapik should use understandable traffic categories.

## Normal

Traffic is flowing normally with little or no significant delay.

## Moderate

Traffic is slower than normal but remains generally moving.

## Heavy

Traffic is significantly slower and causes noticeable travel delays.

## Severe

Traffic is highly congested, with very slow movement or stop-and-go conditions.

The exact classification thresholds should be determined according to the available traffic data and validated during system development.

---

# Route Traffic Summary

After analyzing a route, SanTrapik should provide a concise traffic summary.

Example:

```text
YOUR ROUTE

[SEVERE] SEVERE CONGESTION

Estimated Travel Time
1 hr 24 min

Normal Travel Time
52 min

Estimated Delay
+32 min

Active Incidents
2

Most Affected Road
EDSA – Ortigas Segment

Expected Congestion Relief
10:20 PM
```

The system must clearly distinguish between observed information and AI-generated predictions.

---

# Incident Monitoring

SanTrapik should display road incidents that may cause or contribute to congestion.

Potential incident categories include:

- Vehicular accidents
- Road closures
- Road construction
- Flooding
- Road obstructions
- Traffic signal problems
- Public events
- Vehicle breakdowns
- Other verified or available road incidents

Each incident should contain, when available:

```text
Incident Type
Location
Affected Road
Reported Timestamp
Current Status
Estimated Impact
Expected Resolution/Relief
Data Source
Last Updated
```

---

# Incident Timeline

SanTrapik should provide an incident timeline when sufficient data is available.

Example:

```text
9:12 PM
Accident reported

9:18 PM
Traffic begins increasing

9:31 PM
Congestion reaches severe level

9:47 PM
Emergency response reported

10:05 PM
Traffic begins decreasing

10:20 PM
Expected congestion improvement
```

The system must never fabricate incident events, timestamps, or resolution information.

If an exact event time is unavailable, the interface should indicate that the information is unavailable or use the latest reliable timestamp.

---

# AI/ML Component

AI/ML must be a meaningful component of SanTrapik.

The primary machine-learning objective should be to estimate:

> **When congestion is likely to significantly improve or return toward normal conditions.**

Possible model inputs include:

- Current traffic speed
- Traffic density
- Congestion severity
- Road segment
- Time of day
- Day of week
- Historical congestion patterns
- Incident type
- Incident duration
- Historical incident resolution time
- Weather conditions, if reliable data is available
- Current congestion trend

The system may produce:

```text
Current Congestion
Severe

Current Time
9:15 PM

Predicted Relief
10:05 PM – 10:25 PM

Prediction Confidence
82%
```

The prediction must be presented as an **estimate**, not a guaranteed result.

---

# Observed vs Predicted Information

SanTrapik must clearly distinguish between actual data and model-generated predictions.

## Observed Data

```text
Current speed: 14 km/h
Traffic level: Severe
Incident: Vehicular accident
Incident reported: 9:42 PM
```

## Predicted Data

```text
Expected congestion relief:
10:27 PM

Estimated confidence:
81%
```

The user interface should visually identify predicted information.

---

# AI/ML Technology

The initial machine-learning implementation should use Python-based tools.

Recommended technologies:

- Python
- Pandas
- NumPy
- scikit-learn

Potential algorithms include:

- Random Forest
- Random Forest Regressor
- Gradient Boosting
- Other suitable regression models

XGBoost or LightGBM may be considered if appropriate for the available dataset and project requirements.

The final algorithm should be selected based on experimental evaluation rather than assuming that one algorithm is automatically superior.

---

# Primary ML Prediction

The recommended primary prediction problem is:

> **Predict the estimated number of minutes until congestion relief.**

Example:

```text
Actual relief:
10:30 PM

Predicted relief:
10:24 PM

Prediction error:
6 minutes
```

This can be formulated as a regression problem.

Potential evaluation metrics include:

- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- Mean Absolute Percentage Error (MAPE), where appropriate

If congestion classification is also implemented as an ML task, additional metrics may include:

- Accuracy
- Precision
- Recall
- F1-score

The selected evaluation metrics must correspond to the final ML formulation.

---

# Congestion Heatmap

SanTrapik should provide a Metro Manila traffic heatmap that allows users to quickly identify congested areas.

Legend:

```text
[NORMAL] Normal
[MODERATE] Moderate
[HEAVY] Heavy
[SEVERE] Severe
```

Users should be able to select road segments to view detailed traffic information.

Example:

```text
EDSA – Ortigas Segment

Traffic:
[SEVERE] Severe

Average Speed:
11 km/h

Congestion Started:
8:54 PM

Current Duration:
1 hr 23 min

Active Incident:
Yes

Incident:
Vehicular Accident

Predicted Relief:
10:31 PM
```

---

# Traffic Intelligence Dashboard

SanTrapik should include a traffic intelligence dashboard for broader Metro Manila monitoring.

Example:

```text
SANTRAPIK TRAFFIC INTELLIGENCE

Active Incidents
27

Severe Roads
14

Moderate Roads
31

Average Road Speed
18 km/h


MOST CONGESTED ROADS

1. EDSA          [SEVERE] 91%
2. C-5           [SEVERE] 86%
3. Commonwealth [HEAVY] 73%
4. Ortigas       [HEAVY] 69%


PREDICTED RELIEF

EDSA           10:42 PM
C-5            11:05 PM
Ortigas        10:18 PM
```

The dashboard should support real-time or periodically refreshed information depending on the capabilities of the available data sources.

---

# Route Comparison

When multiple viable routes are available, SanTrapik may compare their traffic conditions.

Example:

```text
ROUTE A
EDSA

Travel Time: 1h 24m
Delay: +32m
Traffic: [SEVERE] Severe
Incidents: 2


ROUTE B
C-5

Travel Time: 1h 08m
Delay: +16m
Traffic: [HEAVY] Heavy
Incidents: 1


RECOMMENDED:
Route B
```

Recommendations should be based on measurable traffic conditions.

---

# Historical Traffic Analysis

SanTrapik should maintain historical traffic information where reliable data is available and legally permitted.

Historical data may be used to identify:

- Typical congestion hours
- Weekday vs. weekend traffic
- Frequently congested roads
- Average congestion duration
- Typical incident duration
- Roads with recurring congestion
- Traffic patterns over time
- Historical incident behavior

Historical information should support both dashboard analytics and machine-learning model development.

---

# Technology Stack

## Frontend

### React.js

React.js should be used to develop the main web application.

Responsibilities include:

- User interface
- Route input
- Interactive map
- Traffic visualization
- Incident markers
- Traffic dashboard
- Charts
- Route comparison
- Prediction display
- Responsive design

### Vite

Vite should be used as the frontend build tool.

### TypeScript

TypeScript should be preferred for improved type safety and maintainability.

### Tailwind CSS

Tailwind CSS should be used for responsive UI development and consistent styling.

---

# Mapping Technology

## MapLibre GL JS

MapLibre GL JS should be used as the primary interactive mapping library.

It provides control over:

- Map rendering
- Road visualization
- Route lines
- Traffic colors
- Incident markers
- Map layers
- Interactive geographic elements

SanTrapik should use map data compatible with OpenStreetMap or another legally permitted mapping provider.

---

# Map Data

## OpenStreetMap

OpenStreetMap may be used as a primary source for geographic and road-map data, subject to its licensing and applicable tile/data-provider requirements.

The project must comply with OpenStreetMap attribution and the terms of any tile provider used.

SanTrapik should not assume that OpenStreetMap itself provides real-time traffic information.

OpenStreetMap is primarily relevant to geographic and road-network data.

---

# Routing

SanTrapik requires a routing engine to determine routes between starting points and destinations.

Potential routing technologies include:

- OSRM
- OpenRouteService

The final routing service should be selected based on:

- Geographic coverage
- API availability
- Routing quality
- Usage limits
- Licensing
- Cost
- Project requirements

The routing system should provide the road geometry needed for subsequent traffic analysis.

---

# Backend

## Python + FastAPI

FastAPI should be used as the main backend framework.

The backend should handle:

- REST API endpoints
- Route processing
- Traffic data processing
- Incident processing
- Data aggregation
- Database communication
- Machine-learning model inference
- Prediction generation
- Data validation
- External API communication

Suggested API structure:

```text
/api/route
/api/traffic
/api/traffic/route
/api/incidents
/api/incidents/{id}
/api/predictions
/api/roads/{id}
```

The exact API structure may change during implementation.

---

# Database

## PostgreSQL + PostGIS

PostgreSQL with the PostGIS extension should be used as the primary database.

PostGIS is recommended because SanTrapik is fundamentally a **geospatial system**.

The application will need to process:

- Latitude and longitude
- Road geometries
- Routes
- Road segments
- Intersections
- Geographic boundaries
- Incident locations
- Incidents near routes
- Spatial relationships between roads and incidents

PostGIS is therefore preferred over a document-oriented database for the core spatial data.

---

# Suggested Database Structure

## road_segments

```text
id
road_name
geometry
direction
city
```

## traffic_records

```text
id
road_segment_id
traffic_level
average_speed
congestion_percentage
timestamp
```

## incidents

```text
id
road_segment_id
incident_type
description
latitude
longitude
reported_at
resolved_at
status
source
last_updated
```

## predictions

```text
id
road_segment_id
predicted_relief_time
predicted_relief_minutes
confidence
created_at
model_version
```

## routes

```text
id
origin
destination
geometry
created_at
```

## traffic_history

```text
id
road_segment_id
traffic_level
average_speed
congestion_percentage
timestamp
```

A `users` table is not required for the current public version because SanTrapik does not currently use user accounts.

---

# Geospatial Processing

PostGIS should be used for spatial operations such as:

- Finding incidents near a route
- Finding road segments intersecting a route
- Determining the geographic location of incidents
- Filtering roads within a geographic area
- Calculating geographic distances
- Associating traffic records with road segments

Example operation:

```text
User Route
    ↓
Route Geometry
    ↓
PostGIS
    ↓
Find incidents near route
    ↓
Determine affected road segments
```

---

# Redis

Redis is an **optional** component.

It may be introduced to improve performance by temporarily caching frequently requested information such as:

- Traffic conditions
- Route results
- Incident data
- Prediction results

Example:

```text
User Request
     ↓
Redis Cache
     ↓
Is data still fresh?
   /       \
 YES       NO
  ↓         ↓
Return    Request new data
          ↓
       Process data
          ↓
       Update cache
```

Redis should not be considered mandatory for the initial prototype.

---

# Data Visualization

## Recharts

Recharts should be used for dashboard charts where appropriate.

Possible visualizations include:

- Traffic trends
- Average speed
- Congestion trends
- Incident counts
- Historical comparisons
- Prediction results

Maps should remain the primary visualization for geographic traffic information.

---

# Data Sources

Reliable data is the most important external dependency of SanTrapik.

The system may use:

- Traffic APIs
- Mapping/routing services
- Government traffic information
- Official road incident reports
- Public traffic datasets
- Historical traffic datasets
- Weather APIs, if relevant
- Verified user-submitted reports, if implemented

Every external data source must be evaluated based on:

- Reliability
- Availability
- Update frequency
- Geographic coverage
- API limitations
- Licensing
- Cost
- Terms of use
- Data completeness

---

# Critical Data-Source Requirement

Before implementing the full SanTrapik system, the development team must first determine:

> **What reliable and legally usable Philippine traffic and incident data is actually available?**

This is the most important technical feasibility requirement of the project.

SanTrapik should not promise functionality that cannot be supported by the available data.

For example, the system should not claim:

```text
Real-time accident detection
```

unless an appropriate data source actually provides sufficiently current accident information.

Likewise, the system should not claim:

```text
Accurate congestion relief prediction
```

until sufficient historical and current data exists to train and evaluate the ML model.

---

# Data-First Development Strategy

Development should follow this order:

```text
1. Identify reliable Philippine traffic data sources
                    ↓
2. Determine available traffic and incident fields
                    ↓
3. Evaluate data quality and update frequency
                    ↓
4. Verify licensing/API usage requirements
                    ↓
5. Collect and prepare historical data
                    ↓
6. Design database schema
                    ↓
7. Build FastAPI data pipeline
                    ↓
8. Build React/MapLibre interface
                    ↓
9. Develop ML prediction model
                    ↓
10. Integrate ML model
                    ↓
11. Evaluate prediction performance
                    ↓
12. Deploy SanTrapik
```

The available data should determine the final technical capabilities of the system.

---

# Data Freshness

Traffic and incident information should contain a timestamp or last-updated value whenever possible.

Example:

```text
Traffic Status
Last updated: 9:54 PM

Incident
Reported: 9:42 PM
Last updated: 9:51 PM
```

SanTrapik should communicate data freshness clearly.

Stale information must not be presented as current real-time information.

---

# Data Integrity

SanTrapik must not fabricate:

- Traffic conditions
- Accident reports
- Incident timestamps
- Road closures
- Relief times
- Traffic statistics
- Prediction confidence
- Historical records

When information is unavailable, the system should explicitly state that the information is unavailable or based on the latest known data.

---

# Route-Specific Traffic Intelligence

This is the central concept of SanTrapik.

Instead of simply showing:

```text
EDSA = [SEVERE]
```

the system should explain:

```text
WHY IS IT RED?
        ↓
Vehicular accident

WHEN DID IT START?
        ↓
9:42 PM

HOW BAD IS IT?
        ↓
Severe

HOW MUCH WILL IT DELAY ME?
        ↓
+32 minutes

WHEN IS IT EXPECTED TO IMPROVE?
        ↓
10:20 PM

IS THERE AN ALTERNATIVE?
        ↓
C-5
```

This feature should distinguish SanTrapik from a basic traffic map.

---

# Positioning Against Existing Navigation Applications

SanTrapik should not be positioned as a direct replacement for Google Maps or other navigation applications.

The system should instead be described as:

> **A traffic intelligence platform focused on understanding congestion, incidents, delays, and expected congestion relief in Philippine roads.**

General navigation applications primarily focus on helping users travel from one location to another.

SanTrapik focuses on explaining the traffic situation affecting that journey.

### SanTrapik focuses on:

- Current congestion severity
- Route-specific traffic conditions
- Incident monitoring
- Incident timestamps
- Congestion duration
- Estimated delay
- Historical traffic patterns
- AI-based congestion prediction
- Expected congestion relief

---

# Key Differentiating Feature

The primary differentiating feature is:

> **Route-specific congestion intelligence with predicted congestion relief time.**

This means the system should not only tell users that a route is congested, but should attempt to explain:

```text
WHERE?
↓
Affected road

WHAT?
↓
Severe congestion

WHY?
↓
Incident

WHEN DID IT START?
↓
Timestamp

HOW LONG HAS IT LASTED?
↓
Duration

HOW MUCH WILL IT DELAY THE USER?
↓
Estimated delay

WHEN MAY IT IMPROVE?
↓
AI prediction

IS THERE AN ALTERNATIVE?
↓
Alternative route
```

---

# System Architecture

```text
                         SANTRAPIK
                            │
                ┌───────────┴───────────┐
                │                       │
           React.js                MapLibre GL JS
                │                       │
                └───────────┬───────────┘
                            │
                         REST API
                            │
                         FastAPI
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
Traffic Service      Incident Service      Route Service
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                   Data Processing Layer
                            │
                ┌───────────┴───────────┐
                │                       │
           PostgreSQL                PostGIS
                │                       │
                └───────────┬───────────┘
                            │
                     Historical Data
                            │
                            ↓
                    Python ML Pipeline
                            │
                            ↓
                  Congestion Prediction
                            │
                            ↓
                  Relief-Time Prediction
```

Optional:

```text
FastAPI
   │
   ↓
Redis Cache
```

---

# Complete Technology Stack

## Frontend

- React.js
- Vite
- TypeScript
- Tailwind CSS

## Mapping

- MapLibre GL JS
- OpenStreetMap-compatible data
- OSRM and/or OpenRouteService

## Backend

- Python
- FastAPI
- Pydantic

## Database

- PostgreSQL
- PostGIS

## AI/ML

- Python
- Pandas
- NumPy
- scikit-learn

## Data Visualization

- Recharts

## Optional Performance Layer

- Redis

## Development Tools

- Git
- GitHub
- Visual Studio Code
- Docker

## Deployment

- Vercel for the React frontend
- Render or Railway for the FastAPI backend
- PostgreSQL/PostGIS hosting compatible with the selected deployment provider

The exact hosting provider may change depending on project requirements, cost, and available resources.

---

# Functional Requirements

## FR-01 — Route Input

The system shall allow users to enter a starting point and destination.

## FR-02 — Route Generation

The system shall generate or retrieve a route between the selected locations.

## FR-03 — Traffic Analysis

The system shall determine the available traffic condition of road segments along the selected route.

## FR-04 — Congestion Classification

The system shall classify traffic congestion into defined severity levels.

## FR-05 — Incident Display

The system shall display available incidents affecting the selected route.

## FR-06 — Incident Timestamp

The system shall display the reported or recorded timestamp of incidents when available.

## FR-07 — Travel Delay Estimation

The system shall calculate or retrieve the estimated delay caused by traffic conditions.

## FR-08 — Congestion Relief Prediction

The system shall use an AI/ML model to estimate when significant congestion relief may occur.

## FR-09 — Traffic Heatmap

The system shall display traffic conditions across supported Metro Manila roads using map-based visualization.

## FR-10 — Historical Analysis

The system shall provide historical traffic information where sufficient data is available.

## FR-11 — Route Comparison

The system shall allow users to compare available routes based on traffic conditions.

## FR-12 — Traffic Dashboard

The system shall provide traffic and incident statistics.

## FR-13 — Data Timestamping

The system shall display the latest available timestamp for traffic and incident information.

## FR-14 — Public Access

The system shall allow users to access the primary traffic-monitoring functionality without creating an account.

---

# Non-Functional Requirements

## Performance

The system should provide traffic information within an acceptable response time under normal network conditions.

## Accuracy

Traffic classifications and ML predictions should be evaluated against available ground-truth or historical data.

## Reliability

The system should gracefully handle unavailable, delayed, incomplete, or inconsistent external data.

## Scalability

The architecture should allow future expansion from Metro Manila to other Philippine cities and regions.

## Usability

Traffic information should be understandable at a glance.

## Security

Although the public system does not currently require accounts, the backend should still use appropriate security practices, including:

- Input validation
- API protection
- Rate limiting where necessary
- Secure API-key storage
- HTTPS
- CORS configuration
- Protection against malicious requests

## Maintainability

The codebase should use a modular architecture separating:

- Frontend
- Backend
- Data processing
- External data integration
- Database
- Machine learning

---

# Future Expansion

Potential future features include:

- User-submitted traffic incidents
- Community traffic reports
- Push notifications
- Saved routes
- Personalized commute monitoring
- Congestion alerts
- Accident severity estimation
- Flood-related road monitoring
- Public transportation congestion analysis
- City-level traffic analytics
- Traffic trend forecasting
- Additional Philippine cities
- Advanced AI models
- Administrative dashboard

These features are not mandatory for the initial implementation.

---

# Initial Project Scope

The initial version should prioritize:

1. Metro Manila road coverage
2. Public access without login/signup
3. Start-point and endpoint route selection
4. Traffic visualization
5. Route-specific congestion analysis
6. Incident visualization
7. Incident timestamps
8. Estimated travel delay
9. Historical traffic data
10. AI-based congestion relief prediction
11. Traffic heatmap
12. Traffic intelligence dashboard
13. Route comparison

The project should remain primarily **software-based** and should not require physical sensors, IoT devices, or dedicated hardware.

---

# Development Principles

The development team should follow these principles:

### Data First

Validate the availability and quality of traffic and incident data before implementing dependent features.

### Evidence Based

Traffic information and predictions must be supported by available data.

### Transparent Predictions

AI predictions must clearly be labeled as predictions or estimates.

### No Fabricated Information

The system must never invent traffic events, incidents, timestamps, or predictions.

### Public Accessibility

The main traffic-monitoring features should remain accessible without requiring user registration.

### Modular Architecture

The system should separate the frontend, backend, data services, database, and ML components.

### Philippines Focus

The initial system should prioritize Philippine roads, particularly Metro Manila, rather than attempting to support worldwide traffic monitoring.

---

# Project Identity

**System Name:** SanTrapik

**System Type:** AI-Powered Web-Based Traffic Intelligence and Road Incident Monitoring System

**Geographic Focus:** Metro Manila, Philippines

**Access Model:** Open to the public; no login/signup required

**Frontend:** React.js + Vite + TypeScript + Tailwind CSS

**Mapping:** MapLibre GL JS + OpenStreetMap-compatible data

**Routing:** OSRM and/or OpenRouteService

**Backend:** Python + FastAPI

**Database:** PostgreSQL + PostGIS

**Machine Learning:** Python + Pandas + NumPy + scikit-learn

**Visualization:** Recharts

**Optional Cache:** Redis

**Deployment:** Vercel + Render/Railway

**Primary AI Focus:** Congestion and congestion-relief prediction

**Primary Differentiator:** Route-specific congestion intelligence with predicted congestion relief time

---

# Core Concept

> **SanTrapik helps users understand what is happening on their route—not just where to go.**

The system should provide a clear, timely, and data-driven view of Philippine road congestion, beginning with Metro Manila.

The ultimate goal is to transform traffic information from a simple **"red road" visualization** into actionable traffic intelligence:

```text
CURRENT CONDITION
        +
INCIDENT INFORMATION
        +
TIMESTAMP
        +
TRAFFIC HISTORY
        +
ESTIMATED DELAY
        +
AI PREDICTION
        ↓
ACTIONABLE TRAFFIC INTELLIGENCE
```
