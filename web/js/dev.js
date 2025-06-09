export const devData = {
    name: 'Ritik',
    company: 'American Express',
    role: 'Software Engineer',
    focus: 'coding',
    resume: `RITIK
Java Backend Developer & Full Stack Engineer
Contact: +91 9991448771 | ritik135001@gmail.com | Portfolio | LinkedIn | GitHub | VitalBite

PROFESSIONAL SUMMARY
Java Backend Developer with 2+ years of experience building scalable enterprise applications and cloud solutions. Proven expertise in Java ecosystem (Spring Boot, Spring Framework), RESTful API development, and database management. Strong background in AWS infrastructure, microservices architecture, and full-stack development. Track record of delivering high-quality enterprise solutions for clients including Amazon and Innovan.

TECHNICAL SKILLS
Backend & Core:

Java, Spring Boot, Spring Framework, Spring Security, Spring Data JPA
RESTful APIs, Microservices Architecture, Web Services (SOAP/REST)
Maven, Gradle, JUnit, Mockito, TestNG

Databases & Data:

PostgreSQL, MongoDB, MySQL, Oracle DB
JPA/Hibernate, Database Design, Query Optimization
Data Modeling, Database Migration, Performance Tuning

Cloud & DevOps:

AWS (CDK, CloudWatch, EC2, RDS, S3), Docker, CI/CD
Jenkins, Git, GitLab, Bitbucket
Infrastructure as Code, Monitoring & Logging

Frontend & Full Stack:

JavaScript, TypeScript, React, Vue.js, Angular
HTML5, CSS3, Tailwind CSS, Responsive Design

Additional Technologies:

AI Integration (OpenAI/Claude/Gemini APIs), Node.js, Python
Agile Methodologies, Jira, Confluence, Postman


PROFESSIONAL EXPERIENCE
SOFTWARE ENGINEER | TEKsystems Global Services
September 2022 – Present
Amazon Inc. | AWS Infrastructure Optimization & Java Code Migration
February 2024 – December 2024

Streamlined AWS infrastructure using Amazon CDK with TypeScript and Java applications
Implemented CloudWatch monitoring and alerts for Java microservices, ensuring 99.9% system availability
Led Java code migration projects, resolving compatibility issues and optimizing performance
Collaborated with cross-functional teams to optimize resource management and deployment strategies
Technologies: Java, AWS CDK, TypeScript, CloudWatch, CloudFormation

Innovan | Government Benefits & Eligibility Platform (Java Backend Focus)
April 2023 – January 2024

Developed robust backend services using Spring Boot and Java for government benefits platform
Designed and implemented RESTful APIs serving critical eligibility and benefits calculation logic
Architected database layer with Oracle DB and MongoDB integration using Spring Data JPA
Built microservices architecture with Docker containerization and Jenkins CI/CD pipelines
Implemented security features using Spring Security for user authentication and authorization
Led sprint refinements and technical discussions with stakeholders
Recognition: Certificate of Appreciation from Innovan & Spot Award from TEKsystems
Technologies: Java, Spring Boot, Spring Security, Spring Data JPA, Oracle DB, MongoDB, Docker, Jenkins

Ruan | Fleet Management System Backend Enhancement
November 2022 – February 2023

Enhanced backend APIs for fleet management system, improving data processing efficiency
Implemented database optimization strategies with PostgreSQL, reducing query response times by 40%
Developed comprehensive API testing suite using Postman and JUnit
Collaborated on bug resolution and system stability improvements
Recognition: Spot Award from TEKsystems
Technologies: Java, PostgreSQL, RESTful APIs, JUnit, Postman


PROJECTS
VitalBite | AI-Powered Nutrition Tracker with Java Backend
January 2025 – February 2025

Developed full-stack nutrition tracking application with Java Spring Boot backend
Implemented RESTful API architecture for nutrition data management and AI integration
Integrated Google Gemini AI with custom Java service layer for intelligent food recognition
Built comprehensive backend with Supabase integration and real-time data synchronization
Developed PWA capabilities with offline support and background sync
Live demo: Vitalbite
Technologies: Java, Spring Boot, React, TypeScript, Google Gemini AI, Supabase, PostgreSQL

Additional Projects

Enterprise Java Applications: Built various Spring Boot microservices with database integration
API Development: Created scalable RESTful APIs with comprehensive documentation
Database Projects: Designed and optimized database schemas for high-performance applications

Additional featured projects available on GitHub

EDUCATION
Bachelor of Technology in Computer Science Engineering
Chandigarh Group of Colleges, India
2018 – 2022

ADDITIONAL SKILLS & CERTIFICATIONS

Java Technologies: Expert in Java 8+, Lambda expressions, Streams API, Collections Framework
Architecture Patterns: MVC, Repository Pattern, Dependency Injection, Design Patterns
API Development: OpenAPI/Swagger documentation, API versioning, Rate limiting
Performance: JVM tuning, Memory management, Profiling, Load testing
Security: OWASP best practices, JWT, OAuth2, Data encryption
Soft Skills: Technical leadership, Client communication, Code reviews, Mentoring
Languages: English (Fluent), Hindi (Native)`,
    objectives: `About the job
Job Title: AI/ML Development Engineer
Company: Nucleus Institute Corp.
Location: Remote (Full-Time)


Company Overview:

At Nucleus Institute, we are dedicated to driving innovation through the creation of advanced AI agents designed to streamline operations and enhance efficiency across various business domains. Our AI solutions are engineered to think, learn, and adapt, automating complex processes while providing deep analytical insights that inform strategic decision-making.


We are seeking a talented AI/ML Development Engineer to join our team. This role offers an exciting opportunity to work on groundbreaking AI/ML projects, crafting the intelligence systems that power our state-of-the-art AI Assistants.


Key Responsibilities:



AI Assistant Development: Lead the development of AI Assistants using Python, with a strong emphasis on Large Language Models (LLMs) and LangChain technologies.
LangChain Expertise: Utilize LangChain Core, Langgraph, Langserve, and LangSmith for building and deploying AI applications, ensuring robust, stateful, and efficient architectures.
Data Pipeline Construction: Build and optimize data pipelines for training and deploying AI models, with a focus on vector databases for efficient data handling.
Backend & API Integration: Implement and manage backend services using FastAPI, and integrate AI features with cloud-based solutions for scalable deployment.
Frontend Development: Develop responsive and intuitive web and mobile interfaces using TypeScript, React, React-Native, and Next.js, ensuring seamless user experiences.
Model Training & Deployment: Utilize Hugging Face frameworks for training, fine-tuning, and deploying Transformer models, including BERT, GPT, and T5.
Proprietary Model Integration: Work with leading AI models from OpenAI, Anthropic, Google, and Meta, focusing on API integration, fine-tuning, and prompt engineering.
Cloud Platforms: Deploy AI solutions on Google Cloud Platform (GCP), with a strong understanding of services like Cloud Run, Cloud Build, and Firebase, as well as familiarity with AWS alternatives.
Cross-functional Collaboration: Collaborate with cross-functional teams, effectively communicating technical concepts to both technical and non-technical stakeholders.
Agile Methodologies: Participate in Agile development practices to ensure efficient and timely project delivery.


Qualifications:



Programming Mastery: Proficiency in Python with a focus on AI/ML applications, including extensive experience with LLMs and LangChain for conversational agents.
AI Frameworks: Strong knowledge of Hugging Face tools, including Transformers, Tokenizers, Datasets, and the Model Hub for state-of-the-art AI development.
Backend & Frontend Expertise: Skilled in using FastAPI for backend development and TypeScript for managing web and mobile interfaces.
Cloud Proficiency: Extensive experience with GCP services, with knowledge of AWS and Azure cloud platforms for deploying and managing AI-driven applications.
Database Experience: Proficient in using vector databases like Pinecone and graph databases such as Neo4j, alongside NoSQL and SQL databases.
Problem-Solving Skills: Demonstrated ability to analyze complex problems and develop innovative AI/ML solutions.
Educational Background: Bachelor’s or Master’s degree in Computer Science or a related field, or equivalent practical experience.

Why Join Us?



As a key member of our team, you will have the opportunity to shape the future of AI by developing cutting-edge AI Assistants and other AI-driven solutions. If you’re passionate about Python programming, AI/ML development, and cloud technologies, we encourage you to apply and be a part of our journey to redefine digital interaction.


Apply Today:`
};

import { devLog } from './config.js';

export function autofillForTesting() {
    devLog("Autofilling form for testing...");
    
    // Get form elements directly from DOM
    const onboardingForm = {
        name: document.getElementById('user-name'),
        company: document.getElementById('user-company'),
        role: document.getElementById('user-role'),
        focusCheckboxes: document.querySelectorAll('input[name="focus"]'),
        resume: document.getElementById('user-resume'),
        objectives: document.getElementById('user-objectives'),
    };
    
    // Check if elements exist before setting values
    if (onboardingForm.name) onboardingForm.name.value = devData.name;
    if (onboardingForm.company) onboardingForm.company.value = devData.company;
    if (onboardingForm.role) onboardingForm.role.value = devData.role;
    
    if (onboardingForm.focusCheckboxes) {
        onboardingForm.focusCheckboxes.forEach(cb => {
            if (cb.value === devData.focus) {
                cb.checked = true;
            }
        });
    }

    if (onboardingForm.resume) onboardingForm.resume.value = devData.resume;
    if (onboardingForm.objectives) onboardingForm.objectives.value = devData.objectives;
    
    devLog("✅ Form autofilled successfully!");
}