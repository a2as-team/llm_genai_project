# LLM GenAI Restaurant Assistant

A production-ready AI-powered restaurant receptionist that handles voice-based conversational interactions. Built with modern cloud-native architecture, the system manages table reservations, food orders, menu inquiries, and general restaurant information through natural dialogue.

## Quick Start

```bash
cd .../llm_genai_project

# Install dependencies with uv
uv sync

# Start the backend API
uv run dev
```

The API will be available at `http://localhost:8000`. To run the complete system locally, you'll also need to start the frontend. See the [Frontend Setup](#frontend-setup) section.

## Architecture

### System Overview

The application follows a distributed architecture with two main components:

**Backend API (This Repository)**
- FastAPI-based REST API serving the AI agent
- Google ADK (Agents Development Kit) for agentic orchestration
- PostgreSQL database for persistent state management
- Containerized with Docker for Cloud Run deployment

**Frontend**
- Next.js React application for real-time voice interactions
- WebSocket connections for bidirectional communication
- Real-time audio streaming and processing
- Repository: [llm_genai_front](https://github.com/PierreB33/llm_and_genai_front)

### Backend Architecture

```
FastAPI Application
│
├── Root Agent (Google ADK)
│   ├── Model: Gemini 2.5 Flash (with native audio preview)
│   ├── Voice: Configurable (Puck voice by default)
│   ├── Language: French (fr-FR)
│   │
│   └── Tools
│       ├── get_menu() - Retrieve full restaurant menu
│       ├── get_informations() - Restaurant details (hours, address, rules)
│       ├── validate_order() - Process and store food orders
│       ├── validate_booking() - Handle table reservations
│       └── cancel_booking() - Manage reservation cancellations
│
├── Database Layer
│   └── PostgreSQL with SQLAlchemy ORM
│       └── Restaurant config, orders, reservations, menu data
│
└── API Endpoints
    ├── /api/livechat - WebSocket for voice interactions
    ├── /api/orders - Order management endpoints
    ├── /api/reservations - Booking endpoints
    └── /health - Health check
```

### Agent Capabilities

The root agent operates as an intelligent restaurant receptionist with the following abilities:

- **Natural Conversation**: Bilingual support with context-aware responses
- **Order Processing**: Takes food orders with menu validation and special requests
- **Reservation Management**: Books tables with capacity checking and availability optimization
- **Menu Intelligence**: Provides detailed menu information, recommendations, and allergen details
- **Business Logic**: Enforces restaurant hours, capacity limits, and operational rules
- **Error Handling**: Gracefully manages invalid requests and provides helpful alternatives

## Tech Stack

### Backend
- **Framework**: FastAPI 0.118+
- **AI/ML**: Google Generative AI SDK, Google ADK (Agents Development Kit)
- **Database**: PostgreSQL 14+ with SQLAlchemy ORM
- **Async Runtime**: asyncpg for non-blocking database access
- **Python**: 3.12+

### Deployment
- **Container**: Docker with multi-stage builds
- **Cloud Platform**: Google Cloud Run
- **Package Manager**: UV (modern Python package manager)


## Setup Instructions

### Prerequisites

- Python 3.12 or higher
- [UV package manager](https://github.com/astral-sh/uv) (install via pip or brew)
- PostgreSQL 14+ instance (local or remote)
- Google Cloud API key with Generative AI access

### Environment Configuration

1. **Create a `.env` file** in the project root:

```bash
cp .env.exemple .env
```

2. **Configure the environment variables**:

```dotenv
# Google Generative AI Configuration
GOOGLE_API_KEY=your_actual_google_api_key_here
MODEL_NAME=gemini-2.5-flash
LIVE_MODEL_NAME=gemini-2.5-flash-native-audio-preview-12-2025
AGENT_VOICE=puck
AGENT_LANGUAGE=fr-FR

# Database Configuration
DB_HOST_SQL=localhost
DB_USER_SQL=postgres
DB_PASSWORD_SQL=your_postgres_password
DB_NAME_SQL=restaurant_ai
DB_PORT_SQL=5432

# Application Settings
APP_NAME=RoyalPizza
ENV=dev
HOST=0.0.0.0
PORT=8000
DEBUG=true

# CORS Configuration (for frontend)
FRONT_ORIGINS=http://localhost:3000
```

### Installation & Running

```bash
# Install dependencies
uv sync

# Run in development mode (with auto-reload)
uv run dev

# Or run in production mode
uv run prod
```

The API will start at `http://localhost:8000` with:
- Interactive API docs at `/docs`
- ReDoc documentation at `/redoc`
- Health check at `/`

### Database Setup

Ensure PostgreSQL is running and the database is initialized:

```bash
# Create database (if not exists)
uv run tests/dbmanagertest.py
```

## Frontend Setup

To run the complete system locally, you need to start the frontend as well:

```bash
# Clone the frontend repository
git clone https://github.com/PierreB33/llm_and_genai_front.git
cd llm_genai_front

# Install dependencies
npm install

# Start development server (runs on port 3000 by default)
npm run dev
```

The frontend will connect to the backend API at `http://localhost:8000/api/livechat`.

## Deployment

### Docker Image

The project includes a `Dockerfile` optimized for Google Cloud Run:

```bash
# Build Docker image locally
docker build -t restaurant-assistant:latest .

# Run container locally
docker run -p 8080:8080 --env-file .env restaurant-assistant:latest
```

### Google Cloud Run

The application is currently deployed on cloud run.

The deployed application is currently running at:
**https://llm-genai-front-162457421857.europe-west9.run.app**

## Project Structure

```
llm_genai_project/
├── src/
│   ├── agents/
│   │   └── root_agent/          # Main ADK agent definition
│   │       └── rootAgent.py      # Root agent with tools and model config
│   ├── app/
│   │   ├── main.py              # FastAPI application factory
│   │   └── api/                 # API route handlers
│   │       ├── livechat.py       # WebSocket endpoint
│   │       ├── orders_reservations.py
│   │       └── health.py
│   ├── bdd/                      # Database layer
│   │   ├── dbmanager.py
│   │   ├── schema.py             # SQLAlchemy models
│   │   └── query.py
│   ├── models/                   # Data models
│   │   ├── booking.py
│   │   └── order_draft.py
│   ├── prompts/
│   │   ├── rootPrompt.py         # System prompt (in French)
│   │   └── validatorPrompt.py
│   ├── tools/                    # Agent tools
│   │   ├── shared_tools/         # Menu, info retrieval
│   │   ├── order_tools/          # Order validation
│   │   └── booking_tools/        # Reservation logic
│   ├── utils/                    # Utilities
│   │   ├── context.py
│   │   ├── restaurant_cache.py   # Runtime config caching
│   │   └── sse_manager.py
│   └── config.py                 # Environment configuration
├── Dockerfile                     # Cloud Run deployment container
├── pyproject.toml                 # UV project definition
├── uv.lock                        # Locked dependencies
└── .env.exemple                   # Environment template
```

## API Endpoints

### Health & Status
- `GET /` - Health check
- `GET /docs` - Swagger UI documentation

### Chat & Interactions
- `WebSocket /api/livechat` - Real-time voice/text interaction endpoint

### Business Logic
- `POST /api/orders/validate` - Validate and process orders
- `POST /api/reservations/validate` - Confirm table reservations
- `POST /api/reservations/cancel` - Cancel existing bookings

## Configuration Reference

### Model Configuration

The agent uses Gemini 2.5 Flash with native audio capabilities:
- **Model**: `gemini-2.5-flash-native-audio-preview-12-2025`
- **Voice**: Configurable (default: "Puck" - upbeat and friendly)
- **Language**: French (fr-FR) with English fallback

### Restaurant Settings

Dynamic configuration injected via `RestaurantCache`:
- Maximum capacity: Configured per location
- Operating hours: Lunch and dinner service windows
- Menu items: Retrieved from database
- Special rules: Applied at validation time


