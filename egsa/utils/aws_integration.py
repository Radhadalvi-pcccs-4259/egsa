"""
AWS Integration Utilities for EGSA Application
Handles S3, RDS, SES, SNS, and CloudWatch integrations
"""

import boto3
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Union
from django.conf import settings
try:
    import pymysql
except ImportError:
    pymysql = None


# AWS Configuration from services-details.txt
AWS_CONFIG = {
    'region_name': 'eu-north-1',
    's3_bucket': 'radha-file-storage-20250731171508',
    'rds_endpoint': 'radha-mysql-production.c7aumg0qarr1.eu-north-1.rds.amazonaws.com',
    'rds_database': 'radha_production_db',
    'rds_username': 'radhaadmin',
    'rds_password': 'RadhaDB123!',
    'ses_email': 'serafinns13@gmail.com',
    'sns_critical_topic': 'arn:aws:sns:eu-north-1:623849686048:radha-critical-events',
    'sns_general_topic': 'arn:aws:sns:eu-north-1:623849686048:radha-general-notifications',
    'cloudwatch_log_group': '/aws/radha/application'
}


class S3Manager:
    """Handles S3 file operations"""
    
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name=AWS_CONFIG['region_name'])
        self.bucket_name = AWS_CONFIG['s3_bucket']
    
    def upload_report(self, file_content: str, file_key: str, content_type: str = 'text/plain') -> bool:
        """Upload report to S3"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=f"reports/{file_key}",
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    'generated_at': datetime.now().isoformat(),
                    'app': 'egsa'
                }
            )
            return True
        except Exception as e:
            logging.error(f"S3 upload error: {e}")
            return False
    
    def download_report(self, file_key: str) -> Optional[str]:
        """Download report from S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=f"reports/{file_key}"
            )
            return response['Body'].read().decode('utf-8')
        except Exception as e:
            logging.error(f"S3 download error: {e}")
            return None
    
    def list_reports(self) -> List[Dict]:
        """List all reports in S3"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix='reports/'
            )
            
            reports = []
            for obj in response.get('Contents', []):
                reports.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'filename': obj['Key'].split('/')[-1]
                })
            return reports
        except Exception as e:
            logging.error(f"S3 list error: {e}")
            return []
    
    def generate_presigned_url(self, file_key: str, expiration: int = 3600) -> Optional[str]:
        """Generate presigned URL for file download"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': f"reports/{file_key}"},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            logging.error(f"S3 presigned URL error: {e}")
            return None


class RDSManager:
    """Handles RDS MySQL operations"""
    
    def __init__(self):
        self.connection_params = {
            'host': AWS_CONFIG['rds_endpoint'],
            'user': AWS_CONFIG['rds_username'],
            'password': AWS_CONFIG['rds_password'],
            'database': AWS_CONFIG['rds_database'],
            'port': 3306
        }
    
    def get_connection(self):
        """Get MySQL connection"""
        try:
            connection = pymysql.connect(**self.connection_params)
            return connection
        except Exception as e:
            logging.error(f"RDS connection error: {e}")
            return None
    
    def store_utility_reading(self, reading_data: Dict) -> bool:
        """Store utility reading in RDS"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            query = """
                INSERT INTO utility_readings 
                (user_id, utility_type, reading_value, unit, cost, reading_date, notes, location)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                reading_data['user_id'],
                reading_data['utility_type'],
                reading_data['reading_value'],
                reading_data['unit'],
                reading_data['cost'],
                reading_data['reading_date'],
                reading_data.get('notes', ''),
                reading_data.get('location', 'Main Building')
            ))
            connection.commit()
            return True
        except Exception as e:
            logging.error(f"RDS insert error: {e}")
            return False
        finally:
            connection.close()
    
    def get_monthly_stats(self, user_id: int, year: int, month: int) -> Dict:
        """Get monthly statistics from RDS"""
        connection = self.get_connection()
        if not connection:
            return {}
        
        try:
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            query = """
                SELECT 
                    utility_type,
                    COUNT(*) as reading_count,
                    SUM(reading_value) as total_usage,
                    SUM(cost) as total_cost,
                    AVG(reading_value) as avg_usage
                FROM utility_readings 
                WHERE user_id = %s 
                AND YEAR(reading_date) = %s 
                AND MONTH(reading_date) = %s
                GROUP BY utility_type
            """
            cursor.execute(query, (user_id, year, month))
            results = cursor.fetchall()
            
            stats = {}
            for row in results:
                stats[row['utility_type']] = {
                    'reading_count': row['reading_count'],
                    'total_usage': float(row['total_usage'] or 0),
                    'total_cost': float(row['total_cost'] or 0),
                    'avg_usage': float(row['avg_usage'] or 0)
                }
            return stats
        except Exception as e:
            logging.error(f"RDS query error: {e}")
            return {}
        finally:
            connection.close()


class SESManager:
    """Handles SES email operations"""
    
    def __init__(self):
        self.ses_client = boto3.client('ses', region_name=AWS_CONFIG['region_name'])
        self.verified_email = AWS_CONFIG['ses_email']
    
    def send_notification_email(self, to_email: str, subject: str, message: str, html_content: Optional[str] = None) -> bool:
        """Send notification email via SES"""
        try:
            email_data = {
                'Source': self.verified_email,
                'Destination': {'ToAddresses': [to_email]},
                'Message': {
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': message}}
                }
            }
            
            if html_content:
                email_data['Message']['Body']['Html'] = {'Data': html_content}
            
            response = self.ses_client.send_email(**email_data)
            return True
        except Exception as e:
            logging.error(f"SES send error: {e}")
            return False
    
    def send_monthly_report_email(self, to_email: str, report_data: Dict) -> bool:
        """Send monthly report via email"""
        subject = f"EGSA Monthly Report - {report_data.get('period', 'Current Month')}"
        
        html_content = f"""
        <html>
        <body>
            <h2>EGSA Monthly Utility Report</h2>
            <p><strong>Period:</strong> {report_data.get('period', 'N/A')}</p>
            <p><strong>Total Cost:</strong> ${report_data.get('total_cost', 0):.2f}</p>
            
            <h3>Efficiency Scores:</h3>
            <ul>
        """
        
        for utility, score in report_data.get('average_efficiency', {}).items():
            html_content += f"<li><strong>{utility.title()}:</strong> {score}</li>"
        
        html_content += f"""
            </ul>
            <p><strong>Cost Trend:</strong> {report_data.get('cost_trend', 'N/A')}</p>
            <p>Generated by EGSA System on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </body>
        </html>
        """
        
        text_content = f"""
        EGSA Monthly Utility Report
        Period: {report_data.get('period', 'N/A')}
        Total Cost: ${report_data.get('total_cost', 0):.2f}
        Cost Trend: {report_data.get('cost_trend', 'N/A')}
        
        Generated by EGSA System
        """
        
        return self.send_notification_email(to_email, subject, text_content, html_content)


class SNSManager:
    """Handles SNS notification operations"""
    
    def __init__(self):
        self.sns_client = boto3.client('sns', region_name=AWS_CONFIG['region_name'])
        self.critical_topic_arn = AWS_CONFIG['sns_critical_topic']
        self.general_topic_arn = AWS_CONFIG['sns_general_topic']
    
    def send_critical_alert(self, message: str, subject: str = "EGSA Critical Alert") -> bool:
        """Send critical alert via SNS"""
        try:
            self.sns_client.publish(
                TopicArn=self.critical_topic_arn,
                Message=message,
                Subject=subject
            )
            return True
        except Exception as e:
            logging.error(f"SNS critical alert error: {e}")
            return False
    
    def send_general_notification(self, message: str, subject: str = "EGSA Notification") -> bool:
        """Send general notification via SNS"""
        try:
            self.sns_client.publish(
                TopicArn=self.general_topic_arn,
                Message=message,
                Subject=subject
            )
            return True
        except Exception as e:
            logging.error(f"SNS general notification error: {e}")
            return False
    
    def send_usage_alert(self, utility_type: str, current_usage: float, threshold: float) -> bool:
        """Send usage threshold alert"""
        if current_usage > threshold:
            message = f"""
            EGSA Usage Alert
            
            Utility Type: {utility_type.title()}
            Current Usage: {current_usage}
            Threshold: {threshold}
            Percentage Over: {((current_usage - threshold) / threshold * 100):.1f}%
            
            Please review usage patterns and consider energy-saving measures.
            """
            return self.send_critical_alert(message, f"High {utility_type.title()} Usage Alert")
        return False


class CloudWatchManager:
    """Handles CloudWatch logging and monitoring"""
    
    def __init__(self):
        self.logs_client = boto3.client('logs', region_name=AWS_CONFIG['region_name'])
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=AWS_CONFIG['region_name'])
        self.log_group = AWS_CONFIG['cloudwatch_log_group']
    
    def log_utility_event(self, event_type: str, data: Dict) -> bool:
        """Log utility event to CloudWatch"""
        try:
            log_event = {
                'timestamp': int(datetime.now().timestamp() * 1000),
                'message': json.dumps({
                    'event_type': event_type,
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                })
            }
            
            # Create log stream if it doesn't exist
            stream_name = f"egsa-{datetime.now().strftime('%Y-%m-%d')}"
            try:
                self.logs_client.create_log_stream(
                    logGroupName=self.log_group,
                    logStreamName=stream_name
                )
            except self.logs_client.exceptions.ResourceAlreadyExistsException:
                pass
            
            # Put log events
            self.logs_client.put_log_events(
                logGroupName=self.log_group,
                logStreamName=stream_name,
                logEvents=[log_event]
            )
            return True
        except Exception as e:
            logging.error(f"CloudWatch logging error: {e}")
            return False
    
    def put_custom_metric(self, metric_name: str, value: float, unit: str = 'Count', utility_type: Optional[str] = None) -> bool:
        """Put custom metric to CloudWatch"""
        try:
            dimensions = [{'Name': 'Application', 'Value': 'EGSA'}]
            if utility_type:
                dimensions.append({'Name': 'UtilityType', 'Value': utility_type})
            
            # Use current UTC time to avoid timezone issues
            from datetime import timezone
            current_time = datetime.now(timezone.utc)
            
            self.cloudwatch_client.put_metric_data(
                Namespace='EGSA/Utilities',
                MetricData=[{
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': unit,
                    'Dimensions': dimensions,
                    'Timestamp': current_time
                }]
            )
            return True
        except Exception as e:
            logging.error(f"CloudWatch metric error: {e}")
            return False
    
    def log_user_action(self, user_id: int, action: str, details: Optional[Dict] = None) -> bool:
        """Log user action for audit trail"""
        event_data = {
            'user_id': user_id,
            'action': action,
            'details': details or {}
        }
        return self.log_utility_event('user_action', event_data)


# Factory class for AWS managers
class AWSManagerFactory:
    """Factory for creating AWS service managers"""
    
    _instances = {}
    
    @classmethod
    def get_s3_manager(cls):
        if 's3' not in cls._instances:
            cls._instances['s3'] = S3Manager()
        return cls._instances['s3']
    
    @classmethod
    def get_rds_manager(cls):
        if 'rds' not in cls._instances:
            cls._instances['rds'] = RDSManager()
        return cls._instances['rds']
    
    @classmethod
    def get_ses_manager(cls):
        if 'ses' not in cls._instances:
            cls._instances['ses'] = SESManager()
        return cls._instances['ses']
    
    @classmethod
    def get_sns_manager(cls):
        if 'sns' not in cls._instances:
            cls._instances['sns'] = SNSManager()
        return cls._instances['sns']
    
    @classmethod
    def get_cloudwatch_manager(cls):
        if 'cloudwatch' not in cls._instances:
            cls._instances['cloudwatch'] = CloudWatchManager()
        return cls._instances['cloudwatch']


# Export classes
__all__ = [
    'S3Manager',
    'RDSManager', 
    'SESManager',
    'SNSManager',
    'CloudWatchManager',
    'AWSManagerFactory',
    'AWS_CONFIG'
]
