## Architecture

The InnoAlias system follows a monolyth architecture with three tiers:  of concerns between frontend, backend, and database layers. The system is designed for scalability, maintainability, and real-time performance.

**Key Dynamic Interactions:**

1. **Presentation tier**: Frontend monolith in its own Docker container
2. **Application tier**: Backend monolith in its own Docker container
3. **Infrastructure tier**: Nginx container, Mongodb container

**📋 Architecture Documentation Status**:
All architectural views (static, dynamic, deployment) are fully documented with UML diagrams, performance tests, and deployment guides in the `docs/architecture/` directory.

**🔧 Required Environment Variables:**
- `SECRET_KEY`: JWT signing secret
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Access token expiration time
- `REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token expiration time
- `DOCKERHUB_USER`: user in docker hub with images of containers (used for CI/CD, only used in docker-compose.yml)
- `GEMINI_API_KEY`: API key for Gemini LLM - needed for AI single player game
- `GEMINI_MODEL_NAME`: Gemini LLM model ID (you have to choose among the available in Google AIStudio)

### Static view

The static architecture of InnoAlias is documented using a UML Component diagram that shows the system's structural components and their relationships. The architecture follows a layered approach with clear boundaries between presentation, business logic, and data layers.

**Key Architectural Components:**

- **Frontend Layer**: React SPA with TypeScript, providing a responsive user interface
- **Backend Layer**: FastAPI-based REST API with WebSocket support for real-time features
- **Database Layer**: MongoDB for document storage with flexible schema
- **Infrastructure Layer**: Nginx reverse proxy for load balancing and SSL termination

**Coupling and Cohesion Analysis:**

The codebase demonstrates **low coupling** through:
- Clear separation between frontend and backend components
- Service-oriented architecture with dedicated routers and services
- Dependency injection pattern for database access
- Interface-based communication between layers

**High cohesion** is achieved through:
- Related functionality grouped in dedicated modules (auth, game, profile)
- Single responsibility principle applied to each service
- Consistent naming conventions and file organization
- Shared utilities and models for common functionality

**Maintainability Impact:**

The design decisions significantly improve maintainability through:
- **Modularity**: Each component can be developed, tested, and deployed independently
- **Testability**: Clear interfaces enable comprehensive unit and integration testing
- **Scalability**: Horizontal scaling possible through containerization and load balancing
- **Technology Flexibility**: Easy to replace individual components without affecting others

**Reference Files:**
- Component Diagram: [`docs/architecture/static-view/component-diagram.png`](docs/architecture/static-view/component-diagram.png)

### Dynamic view

The dynamic architecture is documented using a UML Sequence diagram that illustrates the complete game flow scenario, from user authentication through game creation, gameplay, and leaderboard display. This scenario involves multiple components and demonstrates the system's real-time capabilities.

**Key Dynamic Interactions:**

1. **Authentication Flow**: JWT-based authentication with secure token generation
2. **Game Creation**: REST API calls with database persistence and code generation
3. **Real-time Gameplay**: WebSocket connections for live game updates
4. **State Management**: Coordinated state updates across multiple clients
5. **Game Termination**: Proper cleanup and final score calculation

**Performance Testing:**

The complete game flow scenario has been tested using the provided performance test script. The test measures authentication, game creation, and leaderboard retrieval operations.

**Example Performance Results (from test script):**
- **Authentication**: Average 209ms (min: 203ms, max: 218ms)
- **Game Creation**: Average 2.2ms (min: 1.8ms, max: 2.6ms)
- **Leaderboard Retrieval**: Average 0.9ms (min: 0.7ms, max: 1.3ms)
- **Total Scenario Time**: Average 213ms for complete user journey

**Performance Test Script:**
- Test Implementation: [`docs/architecture/dynamic-view/performance-test.py`](docs/architecture/dynamic-view/performance-test.py)

**Prerequisites:**
1. **Start MongoDB**: `sudo systemctl start mongodb`
2. **Install dependencies**: `python -m pip install -r backend/requirements.txt`
3. **Start backend server**: `python -m uvicorn backend.app.main:app --reload --port 8000`

**Running the Test:**

**Option 1: Automated Script (Recommended)**
```bash
# Run with default settings (localhost:8000, 10 iterations)
./run_performance_test.sh

# Run with custom URL and iterations
./run_performance_test.sh http://localhost:8000 5
```

**Option 2: Manual Steps**
```bash
# 1. Start MongoDB
sudo systemctl start mongodb

# 2. Install dependencies
python -m pip install -r backend/requirements.txt

# 3. Start backend server
python -m uvicorn backend.app.main:app --reload --port 8000

# 4. Run performance test
python docs/architecture/dynamic-view/performance-test.py http://localhost:8000

# 5. Test with custom iterations
python docs/architecture/dynamic-view/performance-test.py http://localhost:8000 --iterations 5

# 6. Test with full stack (requires nginx running)
python docs/architecture/dynamic-view/performance-test.py http://localhost
```

**Reference Files:**
- Sequence Diagram: [`docs/architecture/dynamic-view/game-flow-sequence.png`](docs/architecture/dynamic-view/game-flow-sequence.png)

### Deployment view

The deployment architecture is documented using a custom deployment diagram that shows the physical infrastructure and network topology. The system is designed for containerized deployment with support for both Docker Compose and Kubernetes environments.

**Deployment Architecture:**

- **Client Layer**: Modern web browsers with WebSocket support
- **Load Balancer**: Nginx for high availability
- **Web Server**: Nginx reverse proxy with SSL termination
- **Application Layer**: Containerized frontend and backend services
- **Database Layer**: MongoDB with persistent storage
- **Monitoring**: Optional Prometheus/Grafana stack for observability

**Deployment Choices:**

1. **Containerization**: Docker-based deployment ensures consistency across environments
2. **Microservices**: Independent scaling of frontend and backend components
3. **Reverse Proxy**: Nginx handles SSL termination, static file serving, and WebSocket proxying
4. **Database**: MongoDB chosen for flexible document storage and horizontal scaling
5. **Monitoring**: Built-in health checks and optional metrics collection

**Customer Deployment Options:**

- **Self-Hosted**: Docker Compose for simple deployment
- **Cloud-Native**: Kubernetes for enterprise environments
- **Managed Services**: Integration with cloud provider services
- **On-Premises**: Full control over infrastructure and data

**Reference Files:**
- Deployment Diagram: [`docs/architecture/deployment-view/deployment-diagram.png`](docs/architecture/deployment-view/deployment-diagram.png)
- Deployment Guide: [`docs/architecture/deployment-view/deployment-guide.md`](docs/architecture/deployment-view/deployment-guide.md)
