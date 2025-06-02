# Online Evaluation System

A comprehensive web-based evaluation management platform designed for structured assessment and reporting with advanced analytics and export capabilities.

## 🎯 Project Overview

The Online Evaluation System is a full-stack web application that facilitates the creation, management, and analysis of evaluation templates and assessments. Built with modern technologies, it provides a streamlined solution for organizations to conduct evaluations with real-time analytics and professional reporting features.

### Key Highlights

- **Multi-role User Management**: Administrators, project managers, and evaluators with role-based access control
- **Dynamic Template Creation**: Flexible evaluation templates with customizable criteria and scoring systems
- **Real-time Analytics**: Interactive dashboards with charts, progress tracking, and performance metrics
- **Advanced Export System**: Professional PDF and Excel reports with Korean font support and bulk export capabilities
- **Responsive Design**: Modern UI that works seamlessly across desktop and mobile devices

## ✨ Features

### 📝 Template Management
- Create and customize evaluation templates with multiple criteria
- Flexible scoring systems (1-5 scale, percentage, custom ranges)
- Template versioning and revision tracking
- Duplicate and modify existing templates

### 👥 User & Project Management
- Multi-role authentication system (Admin, Manager, Evaluator)
- Project-based organization with team assignments
- User permission management and access controls
- Company/organization grouping

### 📊 Evaluation Process
- Intuitive evaluation interface with progress saving
- Real-time submission tracking
- Automatic score calculations and validations
- Comment and feedback collection

### 📈 Analytics & Reporting
- Interactive dashboard with Chart.js visualizations
- Real-time progress tracking and completion rates
- Performance analytics and trend analysis
- Comparative evaluation insights

### 📄 Export & Documentation
- **Individual Exports**: PDF and Excel formats for single evaluations
- **Bulk Exports**: ZIP packages with multiple evaluations
- **Professional Formatting**: Korean font support, branded layouts
- **Comprehensive Reports**: Summary sheets with analytics
- **Multiple Formats**: PDF for presentations, Excel for data analysis

## 🛠 Technology Stack

### Frontend
- **React** - Modern component-based UI framework
- **Chart.js** - Interactive data visualization
- **CSS3** - Responsive styling and animations
- **JavaScript ES6+** - Modern JavaScript features

### Backend
- **FastAPI** - High-performance Python web framework
- **SQLAlchemy** - ORM for database management
- **SQLite** - Lightweight database solution
- **Pydantic** - Data validation and serialization

### Export & Reporting
- **ReportLab** - Professional PDF generation
- **OpenPyXL** - Excel file manipulation
- **XlsxWriter** - Advanced Excel features
- **Pandas** - Data processing and analysis

### Development Tools
- **uvicorn** - ASGI server for FastAPI
- **CORS** - Cross-origin resource sharing
- **JWT** - Secure authentication tokens

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Node.js 14 or higher
- npm or yarn package manager

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Online-evaluation
   ```

2. **Set up Python virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python database.py
   ```

5. **Start the backend server**
   ```bash
   uvicorn server:app --reload --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm start
   ```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 📖 Usage Guide

### For Administrators

1. **Initial Setup**
   - Log in with admin credentials
   - Create evaluation templates
   - Set up projects and assign users

2. **Template Creation**
   - Navigate to Templates section
   - Define evaluation criteria and scoring methods
   - Save and activate templates

3. **Project Management**
   - Create new projects
   - Assign templates to projects
   - Manage user permissions and roles

4. **Analytics & Reports**
   - View real-time analytics dashboard
   - Export individual or bulk evaluation reports
   - Generate comprehensive analysis reports

### For Evaluators

1. **Accessing Evaluations**
   - Log in to view assigned evaluations
   - Navigate to active evaluation assignments

2. **Completing Evaluations**
   - Fill out evaluation forms
   - Save progress and submit when complete
   - Add comments and detailed feedback

3. **Tracking Progress**
   - Monitor completion status
   - Review submitted evaluations

## 🔧 API Documentation

The system provides a comprehensive REST API with the following key endpoints:

### Authentication
- `POST /api/login` - User authentication
- `POST /api/register` - User registration

### Templates
- `GET /api/templates` - List all templates
- `POST /api/templates` - Create new template
- `PUT /api/templates/{id}` - Update template
- `DELETE /api/templates/{id}` - Delete template

### Evaluations
- `GET /api/evaluations` - List evaluations
- `POST /api/evaluations` - Submit evaluation
- `GET /api/evaluations/{id}/export` - Export single evaluation
- `POST /api/evaluations/bulk-export` - Bulk export with ZIP

### Analytics
- `GET /api/analytics/dashboard` - Dashboard data
- `GET /api/analytics/progress` - Progress statistics

For complete API documentation, visit http://localhost:8000/docs when running the server.

## 🎨 Export Features

### Single Evaluation Export
- PDF format with professional layout and Korean font support
- Excel format with formatted data and styling
- Instant download with proper filename conventions

### Bulk Export System
- Select multiple evaluations by project or template
- Choose export format (PDF, Excel, or both)
- ZIP compression for easy distribution
- Progress tracking for large exports

### Report Customization
- Company branding and logos
- Custom headers and footers
- Detailed scoring breakdowns
- Comment and feedback inclusion

## 🤝 Contributing

We welcome contributions to improve the Online Evaluation System! Here's how you can help:

### Development Process

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Test thoroughly**
5. **Submit a pull request**

### Code Standards

- Follow PEP 8 for Python code
- Use ESLint configuration for JavaScript
- Write descriptive commit messages
- Include unit tests for new features
- Update documentation as needed

### Reporting Issues

- Use GitHub Issues for bug reports
- Provide detailed reproduction steps
- Include system information and error logs
- Suggest potential solutions when possible

## 📄 License

This project is developed for educational and demonstration purposes. Please contact the repository owner for licensing information.

## 🙋‍♂️ Support

For questions, issues, or feature requests:

- Create an issue on GitHub
- Review the API documentation at `/docs`
- Check the existing issues for similar problems

## 🔄 Version History

### v1.0.0 (Latest)
- Complete evaluation system with template management
- Real-time analytics dashboard
- Advanced export system with PDF/Excel support
- Multi-role user management
- Responsive UI design

## 🎯 Future Enhancements

- Mobile application development
- Advanced analytics with machine learning
- Integration with external systems
- Multi-language support
- Enhanced notification system
- Automated report scheduling

---

**Built with ❤️ for efficient evaluation management**
