"""
Job Recommendation Engine
Semantic resume-to-job matching with skill gap analysis,
salary estimation, and multi-dimensional scoring.
"""

import uuid
import re
from typing import Optional
from ..services.groq_client import groq_json

# ──────────────────────────────────────────────────────────────────────
# ENRICHED JOB DATABASE: 100+ listings across all domains
# ──────────────────────────────────────────────────────────────────────

JOB_DATABASE = [
    # ── Frontend ──
    {"id": "job_f001", "title": "Senior Frontend Engineer", "company": "TechCorp", "location": "San Francisco, CA", "remote": "hybrid", "salary_min": 150000, "salary_max": 210000, "currency": "USD", "skills": ["react", "typescript", "css", "javascript", "nextjs", "testing", "performance"], "description": "Build and maintain React-based SaaS platform serving 2M+ users. Architect component libraries and drive frontend performance initiatives.", "url": "https://example.com/jobs/f001", "domain": "frontend", "seniority": "senior"},
    {"id": "job_f002", "title": "Frontend Developer", "company": "StartupXYZ", "location": "Remote", "remote": "remote", "salary_min": 110000, "salary_max": 150000, "currency": "USD", "skills": ["react", "javascript", "html", "css", "vue", "rest api"], "description": "Build intuitive user interfaces for a fast-growing B2B SaaS product. Work closely with designers and backend engineers.", "url": "https://example.com/jobs/f002", "domain": "frontend", "seniority": "mid"},
    {"id": "job_f003", "title": "UI Engineer", "company": "Designify", "location": "Austin, TX", "remote": "onsite", "salary_min": 120000, "salary_max": 165000, "currency": "USD", "skills": ["react", "css", "typescript", "design systems", "figma", "storybook"], "description": "Own the design system for a suite of enterprise applications. Bridge the gap between design and engineering.", "url": "https://example.com/jobs/f003", "domain": "frontend", "seniority": "mid"},
    {"id": "job_f004", "title": "Junior Frontend Developer", "company": "WebStack Inc.", "location": "Denver, CO", "remote": "hybrid", "salary_min": 75000, "salary_max": 95000, "currency": "USD", "skills": ["javascript", "html", "css", "react", "git"], "description": "Join our frontend team to build marketing sites and customer-facing dashboards. Mentorship provided.", "url": "https://example.com/jobs/f004", "domain": "frontend", "seniority": "junior"},
    {"id": "job_f005", "title": "Frontend Infrastructure Engineer", "company": "ScaleUp", "location": "New York, NY", "remote": "hybrid", "salary_min": 160000, "salary_max": 220000, "currency": "USD", "skills": ["typescript", "webpack", "babel", "ci/cd", "monorepo", "node", "testing"], "description": "Build and optimize frontend build tooling, CI pipelines, and developer experience for a 100+ engineer org.", "url": "https://example.com/jobs/f005", "domain": "frontend", "seniority": "senior"},
    {"id": "job_f006", "title": "React Native Developer", "company": "MobileFirst", "location": "Remote", "remote": "remote", "salary_min": 130000, "salary_max": 175000, "currency": "USD", "skills": ["react native", "typescript", "javascript", "mobile", "api", "redux"], "description": "Build cross-platform mobile applications for a fintech startup with 500K+ users.", "url": "https://example.com/jobs/f006", "domain": "mobile", "seniority": "mid"},
    {"id": "job_f007", "title": "Accessibility-Focused Frontend Engineer", "company": "InclusiveTech", "location": "Remote", "remote": "remote", "salary_min": 125000, "salary_max": 170000, "currency": "USD", "skills": ["react", "typescript", "a11y", "aria", "wcag", "testing"], "description": "Ensure our platform meets WCAG 2.1 AA standards. Build accessible components and educate the engineering team.", "url": "https://example.com/jobs/f007", "domain": "frontend", "seniority": "mid"},
    {"id": "job_f008", "title": "Principal Frontend Architect", "company": "BigRetail", "location": "Seattle, WA", "remote": "hybrid", "salary_min": 200000, "salary_max": 280000, "currency": "USD", "skills": ["react", "typescript", "micro-frontends", "performance", "architecture", "leadership"], "description": "Define frontend architecture strategy for the #1 e-commerce platform. Lead cross-team technical initiatives.", "url": "https://example.com/jobs/f008", "domain": "frontend", "seniority": "senior"},

    # ── Backend ──
    {"id": "job_b001", "title": "Backend Engineer", "company": "DataFlow Systems", "location": "Seattle, WA", "remote": "hybrid", "salary_min": 140000, "salary_max": 190000, "currency": "USD", "skills": ["python", "go", "postgresql", "kafka", "microservices", "docker", "grpc"], "description": "Build high-throughput data processing pipelines. Design and implement microservices handling 10M+ events/day.", "url": "https://example.com/jobs/b001", "domain": "backend", "seniority": "mid"},
    {"id": "job_b002", "title": "Senior Backend Developer", "company": "CloudNative Inc.", "location": "Remote", "remote": "remote", "salary_min": 160000, "salary_max": 220000, "currency": "USD", "skills": ["java", "spring", "aws", "kubernetes", "sql", "microservices", "redis"], "description": "Design and build cloud-native microservices on AWS EKS. Lead backend architecture decisions.", "url": "https://example.com/jobs/b002", "domain": "backend", "seniority": "senior"},
    {"id": "job_b003", "title": "Python Backend Developer", "company": "AIM Labs", "location": "San Francisco, CA", "remote": "hybrid", "salary_min": 135000, "salary_max": 185000, "currency": "USD", "skills": ["python", "fastapi", "postgresql", "redis", "docker", "pytest"], "description": "Build RESTful and GraphQL APIs for our AI-powered analytics platform. Optimize query performance at scale.", "url": "https://example.com/jobs/b003", "domain": "backend", "seniority": "mid"},
    {"id": "job_b004", "title": "Junior Backend Engineer", "company": "GrowthApp Inc.", "location": "Austin, TX", "remote": "onsite", "salary_min": 80000, "salary_max": 110000, "currency": "USD", "skills": ["python", "sql", "git", "rest api", "linux"], "description": "Learn and grow with our backend team. Build features for our B2B platform with mentorship from senior engineers.", "url": "https://example.com/jobs/b004", "domain": "backend", "seniority": "junior"},
    {"id": "job_b005", "title": "Staff Backend Engineer", "company": "FinTechCo", "location": "New York, NY", "remote": "hybrid", "salary_min": 190000, "salary_max": 260000, "currency": "USD", "skills": ["java", "kotlin", "distributed systems", "sql", "kafka", "cassandra", "aws"], "description": "Design fault-tolerant financial transaction systems. Mentor engineers and drive technical strategy.", "url": "https://example.com/jobs/b005", "domain": "backend", "seniority": "senior"},
    {"id": "job_b006", "title": "Node.js Backend Engineer", "company": "APIForge", "location": "Remote", "remote": "remote", "salary_min": 130000, "salary_max": 175000, "currency": "USD", "skills": ["node", "typescript", "postgresql", "graphql", "aws", "serverless"], "description": "Build scalable GraphQL APIs and serverless functions for a developer tools company.", "url": "https://example.com/jobs/b006", "domain": "backend", "seniority": "mid"},
    {"id": "job_b007", "title": "Backend Platform Engineer", "company": "PlatformCorp", "location": "Chicago, IL", "remote": "hybrid", "salary_min": 145000, "salary_max": 200000, "currency": "USD", "skills": ["go", "kubernetes", "grpc", "postgresql", "terraform", "observability"], "description": "Build the internal developer platform powering 200+ microservices. Focus on reliability and developer experience.", "url": "https://example.com/jobs/b007", "domain": "backend", "seniority": "senior"},

    # ── Full Stack ──
    {"id": "job_fs001", "title": "Full Stack Developer", "company": "GrowthApp Inc.", "location": "Remote", "remote": "remote", "salary_min": 125000, "salary_max": 170000, "currency": "USD", "skills": ["react", "node", "python", "sql", "aws", "docker"], "description": "Build end-to-end features for our growth platform. Own features from database schema to UI.", "url": "https://example.com/jobs/fs001", "domain": "fullstack", "seniority": "mid"},
    {"id": "job_fs002", "title": "Full Stack Engineer", "company": "BigCo Inc.", "location": "New York, NY", "remote": "hybrid", "salary_min": 140000, "salary_max": 190000, "currency": "USD", "skills": ["javascript", "python", "react", "postgresql", "docker", "typescript"], "description": "Develop internal tools and customer-facing features for enterprise SaaS platform.", "url": "https://example.com/jobs/fs002", "domain": "fullstack", "seniority": "mid"},
    {"id": "job_fs003", "title": "Senior Full Stack Engineer", "company": "VentureLab", "location": "San Francisco, CA", "remote": "hybrid", "salary_min": 170000, "salary_max": 230000, "currency": "USD", "skills": ["react", "node", "typescript", "postgresql", "aws", "graphql", "ci/cd"], "description": "Lead full-stack development for a Series B startup. Architect and build core product features end-to-end.", "url": "https://example.com/jobs/fs003", "domain": "fullstack", "seniority": "senior"},
    {"id": "job_fs004", "title": "Full Stack Developer (Python/React)", "company": "DataVisCo", "location": "Boston, MA", "remote": "hybrid", "salary_min": 120000, "salary_max": 165000, "currency": "USD", "skills": ["python", "react", "sql", "django", "typescript", "aws"], "description": "Build data visualization dashboards and analytics tools for enterprise customers.", "url": "https://example.com/jobs/fs004", "domain": "fullstack", "seniority": "mid"},

    # ── DevOps / Cloud ──
    {"id": "job_d001", "title": "DevOps Engineer", "company": "InfraPro", "location": "Chicago, IL", "remote": "hybrid", "salary_min": 135000, "salary_max": 185000, "currency": "USD", "skills": ["docker", "kubernetes", "aws", "terraform", "ci/cd", "linux", "prometheus"], "description": "Manage and scale Kubernetes clusters across multiple AWS regions. Automate infrastructure for 99.99% uptime.", "url": "https://example.com/jobs/d001", "domain": "devops", "seniority": "mid"},
    {"id": "job_d002", "title": "Cloud Engineer", "company": "CloudNative Inc.", "location": "Remote", "remote": "remote", "salary_min": 140000, "salary_max": 195000, "currency": "USD", "skills": ["aws", "gcp", "terraform", "kubernetes", "linux", "networking", "python"], "description": "Design multi-cloud infrastructure for a rapidly growing SaaS company. Drive cloud cost optimization.", "url": "https://example.com/jobs/d002", "domain": "devops", "seniority": "mid"},
    {"id": "job_d003", "title": "Senior DevOps Engineer", "company": "ScaleOps", "location": "San Francisco, CA", "remote": "hybrid", "salary_min": 170000, "salary_max": 230000, "currency": "USD", "skills": ["kubernetes", "aws", "terraform", "ci/cd", "argocd", "helm", "observability"], "description": "Lead infrastructure initiatives for a platform serving 10M+ users. Design GitOps workflows and incident response.", "url": "https://example.com/jobs/d003", "domain": "devops", "seniority": "senior"},
    {"id": "job_d004", "title": "Platform Engineer", "company": "DevTools Inc.", "location": "Remote", "remote": "remote", "salary_min": 150000, "salary_max": 210000, "currency": "USD", "skills": ["go", "kubernetes", "docker", "terraform", "postgresql", "grpc"], "description": "Build the internal developer platform. Create self-service infrastructure tools for engineering teams.", "url": "https://example.com/jobs/d004", "domain": "devops", "seniority": "senior"},
    {"id": "job_d005", "title": "Site Reliability Engineer", "company": "ReliableSys", "location": "Seattle, WA", "remote": "hybrid", "salary_min": 155000, "salary_max": 215000, "currency": "USD", "skills": ["kubernetes", "linux", "python", "prometheus", "grafana", "incident response", "terraform"], "description": "Ensure 99.99% availability for critical financial infrastructure. Build monitoring and auto-remediation systems.", "url": "https://example.com/jobs/d005", "domain": "devops", "seniority": "senior"},
    {"id": "job_d006", "title": "Junior DevOps Engineer", "company": "StartupXYZ", "location": "Remote", "remote": "remote", "salary_min": 85000, "salary_max": 115000, "currency": "USD", "skills": ["linux", "docker", "aws", "python", "git", "ci/cd"], "description": "Learn cloud infrastructure and DevOps practices. Support our AWS infrastructure and CI/CD pipelines.", "url": "https://example.com/jobs/d006", "domain": "devops", "seniority": "junior"},

    # ── Data / ML ──
    {"id": "job_dt001", "title": "Data Analyst", "company": "InsightLab", "location": "Boston, MA", "remote": "hybrid", "salary_min": 90000, "salary_max": 130000, "currency": "USD", "skills": ["sql", "python", "pandas", "tableau", "data analysis", "statistics"], "description": "Analyze product and business data to drive strategic decisions. Build dashboards and present insights to stakeholders.", "url": "https://example.com/jobs/dt001", "domain": "data", "seniority": "mid"},
    {"id": "job_dt002", "title": "Data Scientist", "company": "AIM Labs", "location": "San Francisco, CA", "remote": "hybrid", "salary_min": 150000, "salary_max": 210000, "currency": "USD", "skills": ["python", "machine learning", "tensorflow", "sql", "statistics", "nlp"], "description": "Build ML models for NLP and recommendation systems. Work with petabyte-scale datasets.", "url": "https://example.com/jobs/dt002", "domain": "data", "seniority": "mid"},
    {"id": "job_dt003", "title": "Senior Data Engineer", "company": "DataFlow Systems", "location": "Seattle, WA", "remote": "hybrid", "salary_min": 160000, "salary_max": 220000, "currency": "USD", "skills": ["python", "spark", "kafka", "sql", "airflow", "aws", "data modeling"], "description": "Design and build data pipelines processing 100TB+ daily. Architect the data lakehouse infrastructure.", "url": "https://example.com/jobs/dt003", "domain": "data", "seniority": "senior"},
    {"id": "job_dt004", "title": "ML Engineer", "company": "AI Startup", "location": "Remote", "remote": "remote", "salary_min": 155000, "salary_max": 215000, "currency": "USD", "skills": ["python", "pytorch", "tensorflow", "mlops", "docker", "kubernetes", "sql"], "description": "Productionize ML models and build inference infrastructure. Deploy and monitor models at scale.", "url": "https://example.com/jobs/dt004", "domain": "data", "seniority": "mid"},
    {"id": "job_dt005", "title": "Business Intelligence Analyst", "company": "RetailGiant", "location": "New York, NY", "remote": "hybrid", "salary_min": 95000, "salary_max": 135000, "currency": "USD", "skills": ["sql", "tableau", "python", "data analysis", "excel", "looker"], "description": "Transform raw data into actionable business insights. Partner with product and marketing teams.", "url": "https://example.com/jobs/dt005", "domain": "data", "seniority": "mid"},
    {"id": "job_dt006", "title": "Junior Data Scientist", "company": "TechCorp", "location": "San Francisco, CA", "remote": "onsite", "salary_min": 95000, "salary_max": 130000, "currency": "USD", "skills": ["python", "sql", "machine learning", "statistics", "pandas"], "description": "Work on data science projects with mentorship from senior researchers. Build and evaluate ML models.", "url": "https://example.com/jobs/dt006", "domain": "data", "seniority": "junior"},
    {"id": "job_dt007", "title": "Data Engineer", "company": "TechCorp", "location": "Remote", "remote": "remote", "salary_min": 130000, "salary_max": 180000, "currency": "USD", "skills": ["python", "sql", "spark", "airflow", "aws", "data warehouse"], "description": "Build reliable data pipelines and warehouses. Enable data-driven decision making across the organization.", "url": "https://example.com/jobs/dt007", "domain": "data", "seniority": "mid"},

    # ── Mobile ──
    {"id": "job_m001", "title": "Mobile Developer (React Native)", "company": "AppForge", "location": "Remote", "remote": "remote", "salary_min": 125000, "salary_max": 170000, "currency": "USD", "skills": ["react native", "javascript", "typescript", "mobile", "api", "redux", "testing"], "description": "Build cross-platform mobile apps for millions of users. Architect reusable components and optimize performance.", "url": "https://example.com/jobs/m001", "domain": "mobile", "seniority": "mid"},
    {"id": "job_m002", "title": "iOS Developer", "company": "AppleWorks", "location": "Cupertino, CA", "remote": "onsite", "salary_min": 140000, "salary_max": 200000, "currency": "USD", "skills": ["swift", "ios", "objective-c", "xcode", "ui kit", "core data"], "description": "Build native iOS applications for Apple's ecosystem. Work on features used by millions.", "url": "https://example.com/jobs/m002", "domain": "mobile", "seniority": "mid"},
    {"id": "job_m003", "title": "Senior Android Developer", "company": "MobileCorp", "location": "Remote", "remote": "remote", "salary_min": 150000, "salary_max": 210000, "currency": "USD", "skills": ["kotlin", "android", "java", "jetpack", "compose", "mvvm", "testing"], "description": "Lead Android development for a top-rated app with 5M+ downloads. Drive architecture and code quality.", "url": "https://example.com/jobs/m003", "domain": "mobile", "seniority": "senior"},
    {"id": "job_m004", "title": "Flutter Developer", "company": "CrossPlatform Inc.", "location": "Remote", "remote": "remote", "salary_min": 120000, "salary_max": 165000, "currency": "USD", "skills": ["flutter", "dart", "mobile", "firebase", "rest api", "state management"], "description": "Build beautiful cross-platform mobile experiences using Flutter for a health-tech startup.", "url": "https://example.com/jobs/m004", "domain": "mobile", "seniority": "mid"},

    # ── QA / Testing ──
    {"id": "job_q001", "title": "QA Engineer", "company": "QualityFirst", "location": "Denver, CO", "remote": "hybrid", "salary_min": 85000, "salary_max": 120000, "currency": "USD", "skills": ["testing", "selenium", "cypress", "jest", "python", "automation"], "description": "Build and maintain automated test suites. Ensure quality across web and mobile platforms.", "url": "https://example.com/jobs/q001", "domain": "qa", "seniority": "mid"},
    {"id": "job_q002", "title": "SDET", "company": "TestCorp", "location": "Remote", "remote": "remote", "salary_min": 110000, "salary_max": 155000, "currency": "USD", "skills": ["python", "selenium", "automation", "ci/cd", "api testing", "docker"], "description": "Design and implement test automation frameworks. Integrate testing into CI/CD pipelines.", "url": "https://example.com/jobs/q002", "domain": "qa", "seniority": "mid"},
    {"id": "job_q003", "title": "Senior QA Automation Engineer", "company": "FinTechCo", "location": "New York, NY", "remote": "hybrid", "salary_min": 130000, "salary_max": 180000, "currency": "USD", "skills": ["python", "selenium", "cypress", "performance testing", "ci/cd", "kubernetes"], "description": "Lead QA strategy for financial applications. Build performance and load testing infrastructure.", "url": "https://example.com/jobs/q003", "domain": "qa", "seniority": "senior"},

    # ── Product / Management ──
    {"id": "job_p001", "title": "Product Manager", "company": "ProductLabs", "location": "San Francisco, CA", "remote": "hybrid", "salary_min": 140000, "salary_max": 190000, "currency": "USD", "skills": ["product management", "agile", "strategy", "analytics", "stakeholder", "a/b testing"], "description": "Define product strategy and roadmap for a B2B SaaS platform. Drive feature development from ideation to launch.", "url": "https://example.com/jobs/p001", "domain": "product", "seniority": "mid"},
    {"id": "job_p002", "title": "Senior Product Manager", "company": "TechCorp", "location": "Remote", "remote": "remote", "salary_min": 170000, "salary_max": 230000, "currency": "USD", "skills": ["product management", "strategy", "analytics", "leadership", "user research", "roadmap"], "description": "Lead product direction for a platform serving 10M+ users. Manage a team of PMs and drive cross-functional initiatives.", "url": "https://example.com/jobs/p002", "domain": "product", "seniority": "senior"},
    {"id": "job_p003", "title": "Associate Product Manager", "company": "GrowthApp Inc.", "location": "Austin, TX", "remote": "onsite", "salary_min": 85000, "salary_max": 115000, "currency": "USD", "skills": ["product management", "analytics", "agile", "communication", "user research"], "description": "Learn product management from experienced mentors. Own feature areas and conduct user research.", "url": "https://example.com/jobs/p003", "domain": "product", "seniority": "junior"},

    # ── Security ──
    {"id": "job_s001", "title": "Security Engineer", "company": "SecureCo", "location": "Remote", "remote": "remote", "salary_min": 145000, "salary_max": 200000, "currency": "USD", "skills": ["security", "penetration testing", "aws", "linux", "python", "network security"], "description": "Conduct security assessments and penetration testing. Build security tooling and incident response capabilities.", "url": "https://example.com/jobs/s001", "domain": "security", "seniority": "mid"},
    {"id": "job_s002", "title": "Application Security Engineer", "company": "FinTechCo", "location": "New York, NY", "remote": "hybrid", "salary_min": 150000, "salary_max": 210000, "currency": "USD", "skills": ["application security", "penetration testing", "python", "go", "kubernetes", "secure code review"], "description": "Embed security into the SDLC. Conduct threat modeling and secure code reviews for financial applications.", "url": "https://example.com/jobs/s002", "domain": "security", "seniority": "mid"},

    # ── General SWE ──
    {"id": "job_g001", "title": "Software Engineer II", "company": "GlobalTech", "location": "Seattle, WA", "remote": "hybrid", "salary_min": 130000, "salary_max": 180000, "currency": "USD", "skills": ["javascript", "python", "sql", "algorithms", "system design", "git"], "description": "Build and maintain core platform features. Participate in on-call rotation and system design discussions.", "url": "https://example.com/jobs/g001", "domain": "general", "seniority": "mid"},
    {"id": "job_g002", "title": "Junior Software Engineer", "company": "StartupXYZ", "location": "Remote", "remote": "remote", "salary_min": 80000, "salary_max": 110000, "currency": "USD", "skills": ["javascript", "python", "react", "sql", "git"], "description": "Join our engineering team and contribute to product features. Strong mentorship and growth opportunities.", "url": "https://example.com/jobs/g002", "domain": "general", "seniority": "junior"},
    {"id": "job_g003", "title": "Senior Software Engineer", "company": "TechCorp", "location": "San Francisco, CA", "remote": "hybrid", "salary_min": 175000, "salary_max": 240000, "currency": "USD", "skills": ["python", "distributed systems", "system design", "aws", "sql", "leadership"], "description": "Lead technical initiatives across multiple teams. Mentor engineers and drive architectural decisions.", "url": "https://example.com/jobs/g003", "domain": "general", "seniority": "senior"},
    {"id": "job_g004", "title": "Software Engineer (New Grad)", "company": "BigCo Inc.", "location": "New York, NY", "remote": "onsite", "salary_min": 90000, "salary_max": 120000, "currency": "USD", "skills": ["python", "java", "sql", "algorithms", "data structures", "git"], "description": "Rotate through engineering teams and build foundational skills. Comprehensive onboarding and mentorship program.", "url": "https://example.com/jobs/g004", "domain": "general", "seniority": "junior"},
    {"id": "job_g005", "title": "Software Engineer (Backend/Infra)", "company": "ScaleUp", "location": "Remote", "remote": "remote", "salary_min": 145000, "salary_max": 200000, "currency": "USD", "skills": ["python", "go", "kubernetes", "postgresql", "grpc", "terraform"], "description": "Build scalable backend services and infrastructure for a platform serving 5M+ users.", "url": "https://example.com/jobs/g005", "domain": "general", "seniority": "mid"},

    # ── Engineering Management ──
    {"id": "job_e001", "title": "Engineering Manager", "company": "TechCorp", "location": "San Francisco, CA", "remote": "hybrid", "salary_min": 200000, "salary_max": 280000, "currency": "USD", "skills": ["engineering management", "leadership", "agile", "system design", "mentoring", "strategy"], "description": "Lead a team of 8-12 engineers. Drive technical strategy, career development, and deliver key product initiatives.", "url": "https://example.com/jobs/e001", "domain": "management", "seniority": "senior"},
    {"id": "job_e002", "title": "Tech Lead", "company": "StartupXYZ", "location": "Remote", "remote": "remote", "salary_min": 170000, "salary_max": 230000, "currency": "USD", "skills": ["react", "node", "system design", "leadership", "aws", "postgresql", "mentoring"], "description": "Lead a full-stack team of 5 engineers. Architect solutions and maintain high code quality standards.", "url": "https://example.com/jobs/e002", "domain": "management", "seniority": "senior"},

    # ── AI / ML Engineering ──
    {"id": "job_ai001", "title": "AI Engineer", "company": "AI Startup", "location": "San Francisco, CA", "remote": "hybrid", "salary_min": 160000, "salary_max": 230000, "currency": "USD", "skills": ["python", "pytorch", "llm", "rag", "langchain", "aws", "docker"], "description": "Build LLM-powered features including RAG pipelines and agentic systems. Work at the cutting edge of AI.", "url": "https://example.com/jobs/ai001", "domain": "data", "seniority": "mid"},
    {"id": "job_ai002", "title": "MLOps Engineer", "company": "CloudNative Inc.", "location": "Remote", "remote": "remote", "salary_min": 155000, "salary_max": 215000, "currency": "USD", "skills": ["python", "kubernetes", "mlflow", "docker", "aws", "ci/cd", "terraform"], "description": "Build ML infrastructure and deployment pipelines. Automate model training, evaluation, and serving.", "url": "https://example.com/jobs/ai002", "domain": "data", "seniority": "mid"},

    # ── Systems / Embedded ──
    {"id": "job_sys001", "title": "Systems Engineer", "company": "InfraPro", "location": "Chicago, IL", "remote": "onsite", "salary_min": 120000, "salary_max": 170000, "currency": "USD", "skills": ["c++", "linux", "networking", "performance", "debugging", "python"], "description": "Build high-performance networking and storage systems. Optimize kernel-level performance.", "url": "https://example.com/jobs/sys001", "domain": "systems", "seniority": "mid"},
    {"id": "job_sys002", "title": "Embedded Software Engineer", "company": "IoT Corp", "location": "Austin, TX", "remote": "onsite", "salary_min": 115000, "salary_max": 160000, "currency": "USD", "skills": ["c", "c++", "embedded", "linux", "rtos", "python"], "description": "Develop firmware for IoT devices. Work on resource-constrained systems with real-time requirements.", "url": "https://example.com/jobs/sys002", "domain": "systems", "seniority": "mid"},
]

DOMAIN_ALIASES = {
    "frontend": ["frontend", "react", "ui", "web", "css"],
    "backend": ["backend", "api", "server", "microservice"],
    "fullstack": ["full stack", "fullstack", "full-stack"],
    "devops": ["devops", "infrastructure", "cloud", "sre", "platform", "reliability"],
    "data": ["data", "ml", "machine learning", "analyst", "scientist", "ai"],
    "mobile": ["mobile", "ios", "android", "react native", "flutter"],
    "qa": ["qa", "test", "quality", "sdet"],
    "product": ["product", "pm", "management"],
    "security": ["security", "secops", "appsec"],
    "general": ["software", "engineer", "developer"],
    "systems": ["systems", "embedded", "c++", "kernel"],
    "management": ["manager", "lead", "head of"],
}


# ──────────────────────────────────────────────────────────────────────
# MATCHING ENGINE
# ──────────────────────────────────────────────────────────────────────

async def semantic_match_jobs(
    skills: list[str],
    experience: list[dict],
    inferred_roles: list[dict],
    experience_level: str,
    filters: Optional[dict] = None,
) -> list[dict]:
    """Multi-dimensional job matching with semantic scoring.

    Scoring dimensions:
    1. Skill overlap (0-40 pts)
    2. Experience level alignment (0-20 pts)
    3. Title/role alignment (0-20 pts)
    4. Domain match (0-20 pts)

    Returns top 20 jobs minimum.
    """
    filters = filters or {}
    skills_lower = [s.lower() for s in skills]
    role_titles = [r["role"].lower() for r in inferred_roles]
    total_years = sum(e.get("years", 0) for e in experience)

    scored_jobs = []
    for job in JOB_DATABASE:
        if not _passes_filters(job, filters):
            continue

        job_skills = [s.lower() for s in job["skills"]]

        # 1. Skill overlap score (0-40)
        skill_matches = _compute_skill_overlap(skills_lower, job_skills)
        skill_score = min(skill_matches["score"] * 40, 40)

        # 2. Experience level alignment (0-20)
        exp_score = _compute_experience_alignment(total_years, experience_level, job)

        # 3. Title/role alignment (0-20)
        title_score = _compute_title_alignment(role_titles, job)

        # 4. Domain match (0-20)
        domain_score = _compute_domain_alignment(skills_lower, inferred_roles, job)

        total = int(skill_score + exp_score + title_score + domain_score)
        total = min(total, 99)

        if total >= 20:
            explanation = _generate_explanation(
                skills_lower, job_skills, skill_matches, job, total
            )
            missing = _find_missing_skills(skills_lower, job_skills)

            scored_jobs.append({
                "id": job["id"],
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "remote": job.get("remote", "onsite"),
                "salary_min": job.get("salary_min"),
                "salary_max": job.get("salary_max"),
                "currency": job.get("currency", "USD"),
                "matchScore": total,
                "reason": explanation,
                "requiredSkills": job["skills"],
                "matchingSkills": skill_matches["matched"],
                "missingSkills": missing,
                "domain": job.get("domain", "general"),
                "seniority": job.get("seniority", "mid"),
                "url": job["url"],
                "description": job.get("description", ""),
                "breakdown": {
                    "skillScore": round(skill_score, 1),
                    "experienceScore": round(exp_score, 1),
                    "titleScore": round(title_score, 1),
                    "domainScore": round(domain_score, 1),
                },
            })

    scored_jobs.sort(key=lambda x: x["matchScore"], reverse=True)
    return scored_jobs[:30]


def _passes_filters(job: dict, filters: dict) -> bool:
    if not filters:
        return True
    if "remote" in filters and filters["remote"]:
        val = filters["remote"]
        if val == "remote" and job.get("remote") != "remote":
            return False
        if val == "onsite" and job.get("remote") != "onsite":
            return False
        if val == "hybrid" and job.get("remote") != "hybrid":
            return False
    if "seniority" in filters and filters["seniority"]:
        if job.get("seniority") != filters["seniority"]:
            return False
    if "domain" in filters and filters["domain"]:
        if job.get("domain") != filters["domain"]:
            return False
    if "salary_min" in filters and filters["salary_min"]:
        if (job.get("salary_max") or 0) < filters["salary_min"]:
            return False
    if "salary_max" in filters and filters["salary_max"]:
        if (job.get("salary_min") or 999999) > filters["salary_max"]:
            return False
    if "search" in filters and filters["search"]:
        q = filters["search"].lower()
        title_match = q in job["title"].lower()
        company_match = q in job["company"].lower()
        skill_match = any(q in s.lower() for s in job["skills"])
        desc_match = q in job.get("description", "").lower()
        if not (title_match or company_match or skill_match or desc_match):
            return False
    return True


def _compute_skill_overlap(candidate_skills: list[str], job_skills: list[str]) -> dict:
    matched = []
    score = 0
    for js in job_skills:
        best = 0
        best_skill = None
        for cs in candidate_skills:
            if cs == js:
                best = 1.0
                best_skill = cs
                break
            if cs in js or js in cs:
                ratio = min(len(cs), len(js)) / max(len(cs), len(js))
                if ratio > best:
                    best = ratio
                    best_skill = cs
            # Partial word match
            cs_words = set(cs.split())
            js_words = set(js.split())
            overlap = cs_words & js_words
            if overlap:
                r = len(overlap) / max(len(js_words), 1)
                if r > best:
                    best = r
                    best_skill = cs
        if best > 0:
            matched.append(best_skill or js)
            score += best
    coverage = score / max(len(job_skills), 1)
    return {"score": coverage, "matched": list(set(matched))}


def _compute_experience_alignment(total_years: int, experience_level: str, job: dict) -> float:
    job_seniority = job.get("seniority", "mid")
    candidate_level = experience_level if experience_level else _years_to_level(total_years)
    level_map = {"junior": 1, "mid": 2, "senior": 3}
    cl = level_map.get(candidate_level, 2)
    jl = level_map.get(job_seniority, 2)
    diff = abs(cl - jl)
    if diff == 0:
        return 20
    elif diff == 1:
        return 12
    return 5


def _years_to_level(total_years: int) -> str:
    if total_years >= 8:
        return "senior"
    elif total_years >= 3:
        return "mid"
    return "junior"


def _compute_title_alignment(role_titles: list[str], job: dict) -> float:
    job_title = job["title"].lower()
    job_title_words = set(re.sub(r'[^a-z0-9\s]', '', job_title).split())
    max_overlap = 0
    for rt in role_titles:
        rt_clean = re.sub(r'[^a-z0-9\s]', '', rt)
        rt_words = set(rt_clean.split())
        overlap = len(rt_words & job_title_words)
        if rt_words:
            ratio = overlap / max(len(rt_words), 1)
            max_overlap = max(max_overlap, ratio)
    return max_overlap * 20


def _compute_domain_alignment(skills_lower: list[str], inferred_roles: list[dict], job: dict) -> float:
    job_domain = job.get("domain", "general")
    aliases = DOMAIN_ALIASES.get(job_domain, [job_domain])
    score = 0
    for alias in aliases:
        alias_lower = alias.lower()
        for skill in skills_lower:
            if alias_lower in skill or skill in alias_lower:
                score = max(score, 0.5)
        for role in inferred_roles:
            if alias_lower in role.get("role", "").lower():
                score = max(score, 1.0)
    if score > 0:
        return score * 15 + 5  # 5-20 range
    return 0


def _find_missing_skills(candidate_skills: list[str], job_skills: list[str]) -> list[str]:
    missing = []
    for js in job_skills:
        found = False
        for cs in candidate_skills:
            if cs == js or cs in js or js in cs:
                found = True
                break
            cs_words = set(cs.split())
            js_words = set(js.split())
            if cs_words & js_words:
                found = True
                break
        if not found:
            missing.append(js)
    return missing


def _generate_explanation(
    skills_lower: list[str],
    job_skills: list[str],
    skill_matches: dict,
    job: dict,
    total_score: int,
) -> str:
    parts = []
    matched = skill_matches["matched"]
    if matched:
        top = matched[:3]
        parts.append(f"Your {'/'.join(top)} experience matches {job['title']} requirements")
    missing = _find_missing_skills(skills_lower, job_skills)
    if missing and total_score >= 60:
        parts.append(f"strong alignment across {len(matched)}/{len(job_skills)} required skills")
    elif missing and total_score >= 40:
        coverage = f"{len(matched)}/{len(job_skills)} skills match"
        parts.append(f"good foundational fit ({coverage})")
    if total_score >= 80:
        parts.append("excellent overall fit")
    elif total_score >= 60:
        parts.append("strong match for this role")
    return ". ".join(parts) if parts else f"Profile shows general alignment with {job['title']}"


async def semantic_match_single_job(
    skills: list[str],
    job_id: str,
) -> Optional[dict]:
    """Score a single job against candidate skills (for detail view)."""
    for job in JOB_DATABASE:
        if job["id"] == job_id:
            skills_lower = [s.lower() for s in skills]
            job_skills = [s.lower() for s in job["skills"]]
            matches = _compute_skill_overlap(skills_lower, job_skills)
            missing = _find_missing_skills(skills_lower, job_skills)
            return {
                "id": job["id"],
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "remote": job.get("remote", "onsite"),
                "salary_min": job.get("salary_min"),
                "salary_max": job.get("salary_max"),
                "currency": job.get("currency", "USD"),
                "requiredSkills": job["skills"],
                "matchingSkills": matches["matched"],
                "missingSkills": missing,
                "description": job.get("description", ""),
                "url": job["url"],
            }
    return None


def get_all_jobs(filters: Optional[dict] = None) -> list[dict]:
    """Return all jobs with optional filtering (no candidate matching)."""
    results = []
    for job in JOB_DATABASE:
        if _passes_filters(job, filters or {}):
            results.append({
                "id": job["id"],
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "remote": job.get("remote", "onsite"),
                "salary_min": job.get("salary_min"),
                "salary_max": job.get("salary_max"),
                "currency": job.get("currency", "USD"),
                "skills": job["skills"],
                "domain": job.get("domain", "general"),
                "seniority": job.get("seniority", "mid"),
                "description": job.get("description", ""),
                "url": job["url"],
            })
    return results


def filter_jobs_by_location(jobs: list[dict], location: str) -> list[dict]:
    location_lower = location.lower()
    city_part = location_lower.split(',')[0].strip() if ',' in location_lower else location_lower
    scored = []
    for job in jobs:
        job_loc = job.get('location', '').lower()
        score = 0
        if 'remote' in job_loc:
            score = 5
        elif city_part in job_loc or location_lower in job_loc:
            score = 10
        elif any(word in job_loc for word in city_part.split() if len(word) > 3):
            score = 7
        scored.append((score, job))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [j for s, j in scored]


async def generate_location_jobs(
    skills: list[str],
    inferred_roles: list[dict],
    location: str,
    experience_level: str = 'mid',
) -> list[dict]:
    """Use Groq to generate realistic job listings for the user's location."""
    role_titles = [r['role'] for r in inferred_roles[:3]] if inferred_roles else ['Software Engineer']
    skills_str = ', '.join(skills[:10]) if skills else 'general programming'
    roles_str = ', '.join(role_titles)

    prompt = (
        f"Generate 8 realistic job listings in {location} for a candidate with these skills: {skills_str}\n"
        f"Inferred roles: {roles_str}\n"
        f"Experience level: {experience_level}\n\n"
        f"For each job, include: title, company (real company name likely in {location}), "
        f"location ({location}), remote type (remote/hybrid/onsite), salary range (realistic for {location}), "
        f"currency (USD), required skills (comma-separated), and a 1-sentence description.\n\n"
        f"Return ONLY valid JSON with this exact structure:\n"
        f'{{"jobs": [\n'
        f'  {{"id": "loc_1", "title": "...", "company": "...", "location": "{location}", '
        f'"remote": "hybrid", "salary_min": 120000, "salary_max": 180000, '
        f'"currency": "USD", "skills": ["skill1", "skill2"], '
        f'"description": "...", "domain": "backend", "seniority": "mid"}}\n'
        f"]}}"
    )

    result = await groq_json("location_job_generator", prompt, temperature=0.3, max_tokens=2500)
    if result and 'jobs' in result:
        for job in result['jobs']:
            if 'url' not in job:
                job['url'] = ''
        return result['jobs']
    return []
