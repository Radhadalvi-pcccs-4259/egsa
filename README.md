# Django EGSA Application - CI/CD Deployment

## Overview

This is a Django application for managing Electricity, Gas, Steam, and Air Conditioning (EGSA) utilities with AWS cloud services integration and automated CI/CD deployment to EC2.

## Features

- **4-Page Django Application**: Dashboard, Utility Management, Reports, Profile
- **CRUD Operations**: Create, Read, Update, Delete utility readings
- **AWS Integration**: S3, RDS, SES, SNS, CloudWatch
- **Custom Calculator Library**: Object-oriented EGSA calculations
- **Authentication**: Login/Logout functionality
- **Responsive Design**: Bootstrap 5.1.3 with FontAwesome icons
- **Automated CI/CD**: GitHub Actions deployment to EC2

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub Repo   │───▶│ GitHub Actions  │───▶│   EC2 Instance  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   AWS Services  │
                       │  S3 | RDS | SES │
                       │  SNS | CloudWatch│
                       └─────────────────┘
```

## Deployment Infrastructure

- **Region**: eu-north-1 (Stockholm)
- **EC2 Instance**: i-047e93a50b4c5773c
- **Public IP**: 51.21.150.112
- **Application URL**: http://51.21.150.112:8000
- **Admin Panel**: http://51.21.150.112:8000/admin

## GitHub Secrets Configuration

To set up the CI/CD pipeline, you need to configure the following secrets in your GitHub repository:

### Required GitHub Secrets

1. **EC2_SSH_PRIVATE_KEY**: The private key content from `ec2keypair.pem`
2. **EC2_HOST**: `51.21.150.112`
3. **DJANGO_SECRET_KEY**: A secure Django secret key
4. **AWS_ACCESS_KEY_ID**: Your AWS access key ID
5. **AWS_SECRET_ACCESS_KEY**: Your AWS secret access key
6. **AWS_RDS_PASSWORD**: `RadhaDB123!`

### How to Add GitHub Secrets

1. Go to your GitHub repository
2. Click on **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with the exact name and value:

```bash
# Secret Name: EC2_SSH_PRIVATE_KEY
# Secret Value: Copy the entire content of ec2keypair.pem file

# Secret Name: EC2_HOST
# Secret Value: 51.21.150.112

# Secret Name: DJANGO_SECRET_KEY
# Secret Value: Generate a new secret key or use the existing one

# Secret Name: AWS_ACCESS_KEY_ID
# Secret Value: Your AWS access key ID from AdminUser_accessKeys.csv

# Secret Name: AWS_SECRET_ACCESS_KEY
# Secret Value: Your AWS secret access key from AdminUser_accessKeys.csv

# Secret Name: AWS_RDS_PASSWORD
# Secret Value: RadhaDB123!
```

## CI/CD Pipeline Workflow

The GitHub Actions workflow (`.github/workflows/deploy.yml`) performs the following steps:

### 1. Test Phase
- Checks out the repository
- Sets up Python 3.11
- Installs dependencies
- Runs Django tests
- Validates deployment readiness

### 2. Deploy Phase
- Connects to EC2 via SSH
- Stops existing Django application
- Clones the latest repository
- Sets up virtual environment
- Installs dependencies including Gunicorn and WhiteNoise
- Creates environment variables file
- Runs database migrations
- Collects static files
- Creates/updates admin user
- Generates sample data
- Starts production server with Gunicorn

### 3. Verify Phase
- Tests application response
- Confirms successful deployment

### 4. Notify Phase
- Reports deployment status
- Provides access URLs and credentials

## Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd myproject
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r ../requirements.txt
   ```

4. **Run migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser**:
   ```bash
   python manage.py createsuperuser
   ```

6. **Run development server**:
   ```bash
   python manage.py runserver
   ```

## Production Deployment

The application is automatically deployed to EC2 when code is pushed to the `main` or `master` branch. The deployment includes:

- **Web Server**: Gunicorn with 3 workers
- **Static Files**: Served by WhiteNoise
- **Database**: SQLite for development, configurable for RDS MySQL
- **Process Management**: Background process with nohup
- **Logging**: Application and deployment logs

## Access Information

After successful deployment:

- **Application**: http://51.21.150.112:8000
- **Admin Panel**: http://51.21.150.112:8000/admin
- **Admin Login**: `admin` / `admin123`
- **Test User Login**: `testuser` / `testpass123`

## AWS Services Configuration

The application integrates with the following AWS services:

- **S3 Bucket**: `radha-file-storage-20250731171508`
- **RDS MySQL**: `radha-mysql-production.c7aumg0qarr1.eu-north-1.rds.amazonaws.com`
- **SES Email**: `serafinns13@gmail.com`
- **SNS Topics**: Critical events and general notifications
- **CloudWatch**: Application monitoring and logging

## File Structure

```
myproject/
├── .github/workflows/deploy.yml    # CI/CD pipeline
├── myproject/                      # Django project settings
├── egsa/                          # Main application
│   ├── models.py                  # Database models
│   ├── views.py                   # Business logic
│   ├── urls.py                    # URL routing
│   ├── templates/                 # HTML templates
│   └── utils/                     # Custom utilities
│       ├── egsa_calculator.py     # Calculator library
│       └── aws_integration.py     # AWS services
├── static/                        # Static files
├── media/                         # Media uploads
├── deploy_test.sh                 # Local deployment test
└── requirements.txt               # Python dependencies
```

## Troubleshooting

### Common Issues

1. **SSH Connection Failed**: Ensure the private key is correctly added to GitHub secrets
2. **Server Not Starting**: Check EC2 security group allows port 8000
3. **Database Errors**: Verify RDS credentials and network access
4. **Static Files Not Loading**: Check WhiteNoise configuration

### Viewing Logs

SSH into EC2 to view logs:
```bash
ssh -i ec2keypair.pem ec2-user@51.21.150.112
tail -f ~/deployment.log
tail -f ~/myproject/egsa.log
```

### Manual Deployment

If automated deployment fails, you can deploy manually:
```bash
cd ~/myproject
./deploy_test.sh
```

## Security Considerations

- Environment variables for sensitive data
- WhiteNoise for secure static file serving
- HTTPS configurations ready (set SSL flags to True)
- CSRF and security middleware enabled
- Secure headers in production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Push to your fork
6. Create a pull request

The CI/CD pipeline will automatically test and deploy approved changes.

## Support

For issues or questions:
- Check the deployment logs on EC2
- Review GitHub Actions workflow logs
- Verify AWS service configurations
- Contact the development team
