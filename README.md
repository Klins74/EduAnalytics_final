# EduAnalytics - Advanced Educational Analytics Platform

[![CI/CD Pipeline](https://github.com/your-org/eduanalytics/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/your-org/eduanalytics/actions/workflows/ci-cd.yml)
[![Coverage](https://codecov.io/gh/your-org/eduanalytics/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/eduanalytics)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=eduanalytics&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=eduanalytics)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

EduAnalytics is a comprehensive educational analytics platform that integrates with Canvas LMS to provide advanced insights, AI-powered recommendations, and predictive analytics for educational institutions.

## 🚀 Key Features

### 📊 **Advanced Analytics & Reporting**
- **Real-time Dashboards**: Interactive dashboards with course, student, and institutional analytics
- **Predictive Analytics**: ML-powered student performance prediction and risk assessment
- **Attendance Tracking**: Comprehensive attendance and engagement metrics
- **Grade Analytics**: Advanced gradebook analytics with trend analysis

### 🤖 **AI & Machine Learning**
- **AI-Powered Insights**: Intelligent recommendations for students and instructors
- **RAG System**: Retrieval Augmented Generation for contextual content search
- **Performance Prediction**: ML models for student success prediction
- **Chatbot Integration**: AI assistant for educational support
- **Usage Quotas**: Role-based AI request quotas and rate limiting

### 🔗 **Canvas LMS Integration**
- **OAuth2 Authentication**: Secure Canvas API integration
- **Real-time Sync**: Live Events webhook integration for real-time data
- **Data Platform**: Canvas DAP integration for comprehensive data ingestion
- **LTI 1.3 Support**: Full LTI integration with grade passback
- **Assignment Sync**: Bi-directional assignment and submission sync

### 📱 **Modern User Experience**
- **React Frontend**: Modern, responsive web interface
- **Multi-language Support**: i18n support (English, Russian, Kazakh)
- **Role-based Access**: Granular permissions for students, teachers, and admins
- **Mobile Responsive**: Optimized for desktop, tablet, and mobile devices

### 🔔 **Notification System**
- **Multi-channel Notifications**: Email, SMS, Telegram, and in-app notifications
- **Smart Scheduling**: Quiet hours and user preference management
- **Template Engine**: Customizable, localized notification templates
- **Delivery Tracking**: Comprehensive notification delivery analytics

### 🔒 **Security & Privacy**
- **Enterprise Security**: Multiple secrets management backends (Vault, Docker Secrets)
- **Data Retention**: GDPR-compliant data retention and anonymization policies
- **Rate Limiting**: Advanced rate limiting with Redis backend
- **Audit Logging**: Comprehensive audit trails and security monitoring

### 📈 **Observability & Monitoring**
- **OpenTelemetry**: Distributed tracing and metrics collection
- **Grafana Dashboards**: Pre-configured monitoring dashboards
- **Prometheus Metrics**: Application and infrastructure metrics
- **Health Checks**: Comprehensive health and readiness endpoints

## 🏗️ Architecture

### **Backend Stack**
- **FastAPI**: High-performance Python web framework
- **SQLAlchemy 2.0**: Modern ORM with async support
- **PostgreSQL**: Primary database with full-text search
- **Redis**: Caching, rate limiting, and message queuing
- **Alembic**: Database migration management

### **Frontend Stack**
- **React 18**: Modern frontend framework
- **Vite**: Fast build tool and development server
- **Tailwind CSS**: Utility-first CSS framework
- **React Router**: Client-side routing
- **i18next**: Internationalization framework

### **DevOps & Deployment**
- **Docker**: Containerization with multi-stage builds
- **Docker Compose**: Local development and staging deployment
- **GitHub Actions**: CI/CD pipeline with automated testing
- **Multi-environment**: Dev, staging, and production configurations

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/eduanalytics.git
   cd eduanalytics
   ```

2. **Start development environment**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.profiles.yml --profile dev up -d
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Grafana: http://localhost:3001

### Production Deployment

1. **Configure environment**
   ```bash
   cp config/env.production .env
   # Edit .env with your production settings
   ```

2. **Deploy with Docker Compose**
   ```bash
   ./scripts/deploy.sh --environment production --version v1.0.0 --build
   ```

3. **Alternative: Deploy with Docker Swarm**
   ```bash
   docker stack deploy -c docker-compose.yml -c docker-compose.profiles.yml eduanalytics
   ```

## 📖 Documentation

### **API Documentation**
- **Interactive Docs**: Available at `/docs` (Swagger UI)
- **OpenAPI Spec**: Available at `/openapi.json`
- **Postman Collection**: [Download here](docs/EduAnalytics.postman_collection.json)

### **Integration Guides**
- [Canvas LMS Integration](docs/canvas-integration.md)
- [AI Services Setup](docs/ai-integration.md)
- [Notification Configuration](docs/notifications-setup.md)
- [Security Configuration](docs/security-guide.md)

### **Development Guides**
- [Development Setup](docs/development-setup.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Testing Guide](docs/testing-guide.md)
- [Deployment Guide](docs/deployment-guide.md)

## 🔧 Configuration

### **Environment Variables**

| Variable | Description | Default |
|----------|-------------|---------|
| `ENV` | Environment (development/staging/production) | `development` |
| `DATABASE_URL` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection string | - |
| `SECRET_KEY` | Application secret key | - |
| `CANVAS_API_KEY` | Canvas API access key | - |
| `CANVAS_BASE_URL` | Canvas instance URL | - |

### **Secrets Management**

EduAnalytics supports multiple secrets management backends:

- **Docker Secrets**: For Docker Swarm deployments
- **HashiCorp Vault**: For enterprise secret management
- **Environment Variables**: For simple deployments
- **Local Encrypted Files**: For development

Example Vault configuration:
```bash
export VAULT_URL=https://vault.company.com
export VAULT_TOKEN=your-vault-token
export VAULT_SECRET_PATH=secret/eduanalytics
```

## 🧪 Testing

### **Running Tests**
```bash
# All tests
cd server && pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/api/           # API contract tests
```

### **Test Coverage**
- **Unit Tests**: 85%+ coverage requirement
- **Integration Tests**: Key workflows and API endpoints
- **Contract Tests**: API schema validation
- **Smoke Tests**: Production health checks

## 📊 Monitoring & Observability

### **Metrics & Dashboards**
- **Application Metrics**: Request latency, error rates, throughput
- **Business Metrics**: User engagement, course analytics, AI usage
- **Infrastructure Metrics**: CPU, memory, disk, network usage
- **Custom Dashboards**: Role-specific analytics dashboards

### **Alerting**
- **SLA Monitoring**: 99.9% uptime target
- **Performance Alerts**: Response time > 500ms
- **Error Rate Alerts**: Error rate > 1%
- **Business Alerts**: Low engagement, at-risk students

### **Logging**
- **Structured Logging**: JSON format with correlation IDs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Aggregation**: Centralized logging with search capabilities
- **Audit Logs**: Security and compliance event tracking

## 🔐 Security

### **Authentication & Authorization**
- **JWT Tokens**: Secure stateless authentication
- **Role-Based Access Control**: Student, Teacher, Admin roles
- **Canvas SSO**: Single sign-on integration
- **Session Management**: Configurable timeout and refresh

### **Data Protection**
- **Encryption**: AES-256 encryption for sensitive data
- **TLS/SSL**: HTTPS everywhere with certificate management
- **Data Anonymization**: GDPR-compliant data handling
- **Audit Logging**: Complete audit trail for compliance

### **Security Monitoring**
- **Vulnerability Scanning**: Automated dependency scanning
- **Security Headers**: OWASP recommended headers
- **Rate Limiting**: DDoS protection and abuse prevention
- **Intrusion Detection**: Monitoring for suspicious activities

## 🤝 Contributing

We welcome contributions from the community! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on:

- Code of Conduct
- Development workflow
- Pull request process
- Testing requirements
- Documentation standards

### **Development Workflow**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### **Getting Help**
- **Documentation**: Check our comprehensive docs
- **Issues**: Open a GitHub issue
- **Discussions**: Join our GitHub Discussions
- **Email**: support@eduanalytics.com

### **Commercial Support**
For enterprise support, training, and custom development:
- **Email**: enterprise@eduanalytics.com
- **Website**: https://eduanalytics.com

## 🎯 Roadmap

### **Q1 2024**
- [ ] Advanced ML model marketplace
- [ ] Mobile application (React Native)
- [ ] Advanced reporting builder
- [ ] Integration with Google Classroom

### **Q2 2024**
- [ ] Video analytics integration
- [ ] Advanced plagiarism detection
- [ ] Learning path recommendations
- [ ] Parent/guardian portal

### **Q3 2024**
- [ ] Virtual classroom integration
- [ ] Advanced assessment analytics
- [ ] Peer collaboration analytics
- [ ] Accessibility enhancements

## 📈 Analytics Features

### **Student Analytics**
- Performance tracking and predictions
- Engagement pattern analysis
- Learning path optimization
- Risk factor identification
- Personalized recommendations

### **Instructor Analytics**
- Course effectiveness metrics
- Student engagement insights
- Assessment analytics
- Time-to-intervention alerts
- Teaching effectiveness reports

### **Institutional Analytics**
- Cross-course performance analysis
- Resource utilization metrics
- Retention and success rates
- Comparative analytics
- Strategic planning insights

## 🧠 AI Capabilities

### **Machine Learning Models**
- **Performance Prediction**: Predict student success probability
- **Risk Assessment**: Identify at-risk students early
- **Recommendation Engine**: Personalized learning recommendations
- **Engagement Analysis**: Analyze student participation patterns
- **Content Optimization**: Optimize course content effectiveness

### **Natural Language Processing**
- **Content Analysis**: Analyze discussion posts and submissions
- **Sentiment Analysis**: Monitor student sentiment and satisfaction
- **Automated Feedback**: Generate personalized feedback
- **Question Answering**: AI-powered student support chatbot
- **Content Search**: Semantic search across course materials

---

**Built with ❤️ for educators and students worldwide**

*EduAnalytics - Transforming education through data-driven insights*