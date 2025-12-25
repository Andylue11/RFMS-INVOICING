"""
Daily Stock Receiving Report

Generates and emails a daily report of stock received to accounts, admin, sales, and builders.
Runs at 3:45 PM AEST (15:45) on weekdays.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from utils.rfms_client import RFMSClient
from utils.email_sender import EmailSender
import pytz

logger = logging.getLogger(__name__)


class DailyStockReport:
    """
    Generates daily stock receiving reports and emails them to stakeholders.
    """
    
    def __init__(self):
        """Initialize the daily stock report generator"""
        self.rfms_client = RFMSClient()
        self.email_sender = EmailSender()
        
        # Email recipients
        self.recipients = {
            'accounts': os.environ.get('REPORT_EMAIL_ACCOUNTS', 'accounts@atozflooringsolutions.com.au'),
            'admin': os.environ.get('REPORT_EMAIL_ADMIN', 'admin@atozflooringsolutions.com.au'),
            'sales': os.environ.get('REPORT_EMAIL_SALES', 'sales@atozflooringsolutions.com.au'),
            'builders': os.environ.get('REPORT_EMAIL_BUILDERS', 'builders@atozflooringsolutions.com.au')
        }
        
        # From address
        self.from_address = os.environ.get('REPORTS_EMAIL_ADDRESS', 'reports@atozflooringsolutions.com.au')
    
    def get_stock_received_today(self) -> List[Dict]:
        """
        Get all stock received today from database.
        
        Returns:
            List of dictionaries with stock receiving information
        """
        try:
            from models import db, StockReceiving
            from app import app
            
            # Get today's date in AEST
            aest = pytz.timezone('Australia/Brisbane')
            today = datetime.now(aest).date()
            today_str = today.strftime('%Y-%m-%d')
            
            logger.info(f"Fetching stock received for {today_str}")
            
            # Query database for stock received today
            with app.app_context():
                stock_records = StockReceiving.query.filter_by(received_date=today).all()
                received_stock = [record.to_dict() for record in stock_records]
            
            logger.info(f"Found {len(received_stock)} stock receiving records for {today_str}")
            return received_stock
            
        except Exception as e:
            logger.error(f"Error getting stock received today: {e}", exc_info=True)
            return []
    
    
    def generate_report_html(self, stock_records: List[Dict]) -> str:
        """
        Generate HTML report from stock receiving records.
        
        Args:
            stock_records: List of stock receiving records
            
        Returns:
            HTML string for the report
        """
        aest = pytz.timezone('Australia/Brisbane')
        today = datetime.now(aest).strftime('%A, %d %B %Y')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .summary {{ margin-top: 20px; padding: 15px; background-color: #e7f3ff; border-left: 4px solid #2196F3; }}
            </style>
        </head>
        <body>
            <h1>Daily Stock Receiving Report</h1>
            <p><strong>Date:</strong> {today}</p>
            <p><strong>Total Records:</strong> {len(stock_records)}</p>
            
            <table>
                <thead>
                    <tr>
                        <th>Order Number</th>
                        <th>Sold To / Ship To</th>
                        <th>City/Suburb</th>
                        <th>Supplier</th>
                        <th>Stock Received</th>
                        <th>Quantity</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        if not stock_records:
            html += """
                    <tr>
                        <td colspan="6" style="text-align: center; padding: 20px;">
                            No stock received today.
                        </td>
                    </tr>
            """
        else:
            for record in stock_records:
                city_suburb = record.get('city_suburb', '') or 'N/A'
                if record.get('is_st_order'):
                    city_suburb = 'N/A (General Warehouse)'
                
                html += f"""
                    <tr>
                        <td><strong>{record.get('order_number', 'N/A')}</strong></td>
                        <td>{record.get('sold_to_name', 'Unknown')}</td>
                        <td>{city_suburb}</td>
                        <td>{record.get('supplier_name', 'Unknown')}</td>
                        <td>{record.get('stock_received', 'N/A')}</td>
                        <td>{record.get('quantity', 0)} {record.get('unit', '')}</td>
                    </tr>
                """
        
        html += """
                </tbody>
            </table>
            
            <div class="summary">
                <p><strong>Note:</strong> Orders starting with "#ST" are General Warehouse stock and are allocated to jobs/orders as needed.</p>
                <p>This report is automatically generated daily at 3:45 PM AEST.</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_report(self) -> bool:
        """
        Generate and send the daily stock receiving report.
        
        Returns:
            True if report sent successfully, False otherwise
        """
        try:
            logger.info("Generating daily stock receiving report...")
            
            # Get stock received today
            stock_records = self.get_stock_received_today()
            
            # Generate HTML report
            report_html = self.generate_report_html(stock_records)
            
            # Prepare email
            aest = pytz.timezone('Australia/Brisbane')
            today = datetime.now(aest).strftime('%A, %d %B %Y')
            subject = f"Daily Stock Receiving Report - {today}"
            
            # Send to all recipients
            all_recipients = list(self.recipients.values())
            success_count = 0
            
            for recipient in all_recipients:
                try:
                    if self.email_sender.send_email(
                        from_address=self.from_address,
                        to_address=recipient,
                        subject=subject,
                        body=report_html,
                        body_type='HTML'
                    ):
                        success_count += 1
                        logger.info(f"Report sent successfully to {recipient}")
                    else:
                        logger.error(f"Failed to send report to {recipient}")
                except Exception as e:
                    logger.error(f"Error sending report to {recipient}: {e}", exc_info=True)
            
            if success_count == len(all_recipients):
                logger.info(f"Daily stock report sent successfully to all {len(all_recipients)} recipients")
                return True
            elif success_count > 0:
                logger.warning(f"Daily stock report sent to {success_count} of {len(all_recipients)} recipients")
                return True  # Partial success
            else:
                logger.error("Failed to send daily stock report to any recipients")
                return False
                
        except Exception as e:
            logger.error(f"Error generating/sending daily stock report: {e}", exc_info=True)
            return False


def schedule_daily_report():
    """
    Schedule the daily stock report to run at 3:45 PM AEST on weekdays.
    This should be called when the Flask app starts.
    """
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    import pytz
    
    scheduler = BackgroundScheduler()
    
    # AEST timezone
    aest = pytz.timezone('Australia/Brisbane')
    
    # Schedule for 3:45 PM AEST (15:45) on weekdays (Monday-Friday)
    scheduler.add_job(
        func=run_daily_report,
        trigger=CronTrigger(
            hour=15,
            minute=45,
            timezone=aest,
            day_of_week='mon-fri'  # Monday to Friday
        ),
        id='daily_stock_report',
        name='Daily Stock Receiving Report',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Daily stock report scheduler started - will run at 3:45 PM AEST on weekdays")
    
    return scheduler


def run_daily_report():
    """
    Function to run the daily report (called by scheduler).
    """
    try:
        report = DailyStockReport()
        report.send_report()
    except Exception as e:
        logger.error(f"Error running daily stock report: {e}", exc_info=True)

