# GitHub Actions CI/CD Setup Guide

## Step-by-Step Setup Instructions

### 1. Prepare Your Repository

1. Ensure your Django project is pushed to a GitHub repository
2. Make sure the repository has the following structure:
   ```
   your-repo/
   ├── .github/workflows/deploy.yml
   ├── myproject/
   ├── requirements.txt
   └── README.md
   ```

### 2. Generate Django Secret Key

Run the secret key generator:
```bash
cd e:\radha_cpp
python generate_secret_key.py
```

Copy the generated secret key for use in GitHub secrets.

### 3. Prepare EC2 Private Key

1. Locate your `ec2keypair.pem` file
2. Open it in a text editor
3. Copy the ENTIRE content including the header and footer:
   ```
   -----BEGIN RSA PRIVATE KEY-----
   [key content]
   -----END RSA PRIVATE KEY-----
   ```

### 4. Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these 6 secrets:

#### EC2_SSH_PRIVATE_KEY
```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
[Your complete private key content from ec2keypair.pem]
...
-----END RSA PRIVATE KEY-----
```

#### EC2_HOST
```
51.21.150.112
```

#### DJANGO_SECRET_KEY
```
[Generated secret key from step 2]
```

#### AWS_ACCESS_KEY_ID
```
[From AdminUser_accessKeys.csv - Access key ID column]
```

#### AWS_SECRET_ACCESS_KEY
```
[From AdminUser_accessKeys.csv - Secret access key column]
```

#### AWS_RDS_PASSWORD
```
RadhaDB123!
```

### 5. Verify EC2 Security Group

Ensure your EC2 security group allows:
- Port 22 (SSH) from your IP
- Port 8000 (HTTP) from anywhere (0.0.0.0/0)

### 6. Test SSH Connection (Optional)

Test SSH connection to EC2:
```bash
ssh -i ec2keypair.pem ec2-user@51.21.150.112
```

### 7. Push Code to Trigger Deployment

1. Make any change to your code
2. Commit and push to main/master branch:
   ```bash
   git add .
   git commit -m "Setup CI/CD deployment"
   git push origin main
   ```

### 8. Monitor Deployment

1. Go to your GitHub repository
2. Click on "Actions" tab
3. Watch the deployment workflow progress
4. Check for any errors in the logs

### 9. Verify Deployment

After successful deployment:
- Visit: http://51.21.150.112:8000
- Login with: admin / admin123
- Test all 4 pages: Dashboard, Utilities, Reports, Profile

## Expected Deployment Timeline

- **Test Phase**: 2-3 minutes
- **Deploy Phase**: 5-10 minutes
- **Verify Phase**: 1 minute
- **Total**: 8-14 minutes

## Deployment Process Details

### What Happens During Deployment:

1. **GitHub Actions Runner**:
   - Checks out your code
   - Sets up Python environment
   - Runs tests

2. **EC2 Connection**:
   - Connects via SSH using your private key
   - Stops any running Django processes

3. **Code Deployment**:
   - Clones fresh repository
   - Sets up virtual environment
   - Installs dependencies

4. **Django Setup**:
   - Runs database migrations
   - Collects static files
   - Creates admin user
   - Generates sample data

5. **Server Start**:
   - Starts Gunicorn server on port 8000
   - Runs in background with nohup

### Environment Variables Created on EC2:

```bash
DJANGO_SECRET_KEY=<your-secret-key>
DEBUG=False
ALLOWED_HOSTS=51.21.150.112,localhost,127.0.0.1
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>
AWS_DEFAULT_REGION=eu-north-1
AWS_S3_BUCKET_NAME=radha-file-storage-20250731171508
AWS_RDS_ENDPOINT=radha-mysql-production.c7aumg0qarr1.eu-north-1.rds.amazonaws.com
AWS_RDS_USERNAME=radhaadmin
AWS_RDS_PASSWORD=RadhaDB123!
AWS_RDS_DATABASE=radha_production_db
AWS_SES_EMAIL=serafinns13@gmail.com
AWS_SNS_CRITICAL_TOPIC=arn:aws:sns:eu-north-1:623849686048:radha-critical-events
AWS_SNS_GENERAL_TOPIC=arn:aws:sns:eu-north-1:623849686048:radha-general-notifications
```

## Troubleshooting Common Issues

### 1. SSH Connection Failed
- **Error**: "Permission denied (publickey)"
- **Solution**: Ensure EC2_SSH_PRIVATE_KEY secret contains the complete private key with headers

### 2. Server Won't Start
- **Error**: "Address already in use"
- **Solution**: The workflow kills existing processes, but you can manually check:
  ```bash
  ssh -i ec2keypair.pem ec2-user@51.21.150.112
  pkill -f gunicorn
  pkill -f runserver
  ```

### 3. Dependencies Installation Failed
- **Error**: "pip install failed"
- **Solution**: Check if requirements.txt is in the repository root

### 4. Database Migration Errors
- **Error**: "Migration failed"
- **Solution**: The workflow recreates the SQLite database on each deployment

### 5. Static Files Not Loading
- **Error**: "Static files 404"
- **Solution**: WhiteNoise is configured to serve static files automatically

## Manual Deployment (Fallback)

If automated deployment fails, you can deploy manually:

```bash
# SSH into EC2
ssh -i ec2keypair.pem ec2-user@51.21.150.112

# Clone repository
git clone https://github.com/your-username/your-repo.git
cd your-repo/myproject

# Run deployment script
chmod +x deploy_test.sh
./deploy_test.sh

# Start server
nohup gunicorn --bind 0.0.0.0:8000 myproject.wsgi:application &
```

## Monitoring and Logs

### View Deployment Logs:
```bash
ssh -i ec2keypair.pem ec2-user@51.21.150.112
tail -f ~/deployment.log
```

### View Application Logs:
```bash
tail -f ~/myproject/egsa.log
```

### Check Server Status:
```bash
ps aux | grep gunicorn
curl http://localhost:8000
```

## Security Best Practices

1. **Never commit secrets to repository**
2. **Use GitHub Secrets for all sensitive data**
3. **Regularly rotate AWS access keys**
4. **Keep EC2 security groups restrictive**
5. **Monitor deployment logs for suspicious activity**

## Updating the Application

Every time you push code to main/master branch:
1. GitHub Actions automatically triggers
2. Tests run first (deployment stops if tests fail)
3. If tests pass, deployment proceeds
4. Application is updated with zero-downtime using the new code

This ensures your EC2 instance always runs the latest version of your code!
