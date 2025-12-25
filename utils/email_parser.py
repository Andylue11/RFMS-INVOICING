"""
Email Parser Utility for Outlook .msg files
Extracts email metadata, body, and attachments
"""

import logging
import os
import re
from typing import Dict, List, Optional, Tuple
import uuid
from email.utils import parseaddr

logger = logging.getLogger(__name__)

try:
    import extract_msg
    EXTRACT_MSG_AVAILABLE = True
except ImportError:
    EXTRACT_MSG_AVAILABLE = False
    logger.warning("extract_msg library not available. Email parsing will be limited.")


class EmailParser:
    """Parser for Outlook .msg files"""
    
    def __init__(self, msg_path: str):
        """
        Initialize email parser with path to .msg file
        
        Args:
            msg_path: Path to the .msg file
        """
        self.msg_path = msg_path
        if not os.path.exists(msg_path):
            raise FileNotFoundError(f"Email file not found: {msg_path}")
    
    def _format_date(self, date_value) -> str:
        """
        Format date value to string. Handles both datetime objects and strings.
        
        Args:
            date_value: Date value (datetime object, string, or None)
            
        Returns:
            Formatted date string or empty string
        """
        if not date_value:
            return ''
        
        try:
            # If it's already a string, return it
            if isinstance(date_value, str):
                return date_value
            
            # If it's a datetime object, format it
            if hasattr(date_value, 'strftime'):
                return date_value.strftime('%Y-%m-%d %H:%M:%S')
            
            # Otherwise, convert to string
            return str(date_value)
        except Exception as e:
            logger.warning(f"Error formatting date: {e}")
            return str(date_value) if date_value else ''
    
    def _extract_email_from_body(self, body_text: str) -> Optional[Tuple[str, str]]:
        """
        Extract email address from the email body text.
        Looks for forwarded email patterns like:
        - "From: Name <email@domain.com>"
        - "Reply To: Name <email@domain.com>"
        - "Reply-To: Name <email@domain.com>"
        
        Args:
            body_text: The email body text to parse
            
        Returns:
            Tuple of (name, email) if found, None otherwise
        """
        if not body_text:
            return None
        
        # Pattern 1: "Reply To:" or "Reply-To:" followed by name and email
        # Examples: "Reply To: John Smith <john@example.com>"
        reply_to_pattern = r'(?:Reply\s*[-:]?\s*To\s*:?\s*)(.+?)\s*<([^>]+@[^>]+)>'
        match = re.search(reply_to_pattern, body_text, re.IGNORECASE | re.MULTILINE)
        if match:
            name = match.group(1).strip()
            email = match.group(2).strip()
            logger.info(f"Found Reply-To in body: {name} <{email}>")
            return (name, email)
        
        # Pattern 2: "From:" followed by name and email (for forwarded emails)
        # Examples: "From: John Smith <john@example.com>"
        # Only match if it's early in the body (first 2000 chars) to avoid matching in regular text
        from_pattern = r'(?:^|\n)\s*From\s*:?\s*(.+?)\s*<([^>]+@[^>]+)>'
        matches = list(re.finditer(from_pattern, body_text[:2000], re.IGNORECASE | re.MULTILINE))
        if matches:
            # Take the first match (most likely the forwarded email)
            match = matches[0]
            name = match.group(1).strip()
            email = match.group(2).strip()
            # Skip if it's clearly just the sender (contains common email patterns we want to avoid)
            if '@' in name or len(name) > 100:  # Likely malformed
                return None
            logger.info(f"Found From in body: {name} <{email}>")
            return (name, email)
        
        return None
    
    def parse(self) -> Dict:
        """
        Parse the .msg file and extract all relevant information
        
        Returns:
            Dict containing email metadata, body, and attachment info
        """
        if not EXTRACT_MSG_AVAILABLE:
            raise ImportError("extract_msg library is required. Install it with: pip install extract-msg")
        
        try:
            msg = extract_msg.Message(self.msg_path)
            
            # Extract email metadata
            sender_name, sender_email = ('', '')
            if hasattr(msg, 'sender') and msg.sender:
                try:
                    parsed = parseaddr(str(msg.sender))
                    sender_name = parsed[0] or ''
                    sender_email = parsed[1] or ''
                except Exception as e:
                    logger.warning(f"Error parsing sender address: {e}")
                    sender_email = str(msg.sender) if msg.sender else ''
            elif hasattr(msg, 'senderEmail') and msg.senderEmail:
                sender_email = str(msg.senderEmail)
                sender_name = str(getattr(msg, 'senderName', '')) if getattr(msg, 'senderName', None) else ''
            
            # Try to get reply-to email (not all .msg files have this field)
            reply_to = sender_email  # Default to sender email
            if hasattr(msg, 'replyTo') and msg.replyTo:
                try:
                    parsed_reply = parseaddr(str(msg.replyTo))
                    reply_to = parsed_reply[1] if parsed_reply[1] else sender_email
                except Exception as e:
                    logger.warning(f"Error parsing replyTo address: {e}")
                    reply_to = sender_email
            elif hasattr(msg, 'replyToEmail') and msg.replyToEmail:
                reply_to = str(msg.replyToEmail)
            elif hasattr(msg, 'reply_to') and msg.reply_to:
                try:
                    parsed_reply = parseaddr(str(msg.reply_to))
                    reply_to = parsed_reply[1] if parsed_reply[1] else sender_email
                except Exception as e:
                    logger.warning(f"Error parsing reply_to address: {e}")
                    reply_to = sender_email
            
            subject = msg.subject or '' if hasattr(msg, 'subject') else ''
            
            # Extract body text and HTML, ensuring they're strings
            body_text_raw = msg.body if (hasattr(msg, 'body') and msg.body) else None
            body_html_raw = msg.htmlBody if (hasattr(msg, 'htmlBody') and msg.htmlBody) else None
            
            # Convert to string if bytes
            body_text = ''
            if body_text_raw:
                if isinstance(body_text_raw, bytes):
                    try:
                        body_text = body_text_raw.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            body_text = body_text_raw.decode('latin-1')
                        except UnicodeDecodeError:
                            body_text = body_text_raw.decode('utf-8', errors='replace')
                else:
                    body_text = str(body_text_raw)
            
            body_html = ''
            if body_html_raw:
                if isinstance(body_html_raw, bytes):
                    try:
                        body_html = body_html_raw.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            body_html = body_html_raw.decode('latin-1')
                        except UnicodeDecodeError:
                            body_html = body_html_raw.decode('utf-8', errors='replace')
                else:
                    body_html = str(body_html_raw)
            
            # Try to extract reply-to email from body (for forwarded emails)
            # Convert HTML to text for parsing if needed
            body_for_parsing = body_text
            if body_html and not body_text:
                # Try to extract text from HTML for parsing
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(body_html, 'html.parser')
                    body_for_parsing = soup.get_text()
                except:
                    body_for_parsing = body_html
            
            # Extract reply-to from body if not found in header
            reply_to_name = None
            if reply_to == sender_email:  # Only if we didn't find it in headers
                body_reply = self._extract_email_from_body(body_for_parsing)
                if body_reply:
                    reply_to_name, reply_to_email = body_reply
                    reply_to = reply_to_email
                    logger.info(f"Using reply-to from email body: {reply_to_name} <{reply_to}>")
            
            # Extract attachments info (don't save yet, just get metadata)
            attachments_info = []
            if hasattr(msg, 'attachments') and msg.attachments is not None:
                try:
                    for attachment in msg.attachments:
                        try:
                            if hasattr(attachment, 'longFilename') and attachment.longFilename:
                                filename = str(attachment.longFilename)
                            elif hasattr(attachment, 'shortFilename') and attachment.shortFilename:
                                filename = str(attachment.shortFilename)
                            else:
                                filename = f"attachment_{len(attachments_info)}"
                            
                            # Get attachment size (with safe access)
                            size = 0
                            try:
                                if hasattr(attachment, 'data'):
                                    data = attachment.data
                                    if data:
                                        if isinstance(data, (bytes, bytearray)):
                                            size = len(data)
                                        elif isinstance(data, str):
                                            # If it's a string, encode it to bytes to get size
                                            size = len(data.encode('utf-8'))
                                        else:
                                            try:
                                                size = len(str(data))
                                            except:
                                                size = 0
                            except Exception as e:
                                logger.debug(f"Could not get attachment size: {e}")
                                size = 0
                            
                            # Get content type
                            content_type = 'application/octet-stream'
                            if hasattr(attachment, 'type') and attachment.type:
                                content_type = str(attachment.type)
                            
                            attachments_info.append({
                                'filename': filename,
                                'size': size,
                                'content_type': content_type
                            })
                        except Exception as e:
                            logger.warning(f"Error processing attachment metadata: {e}")
                            continue
                except Exception as e:
                    logger.warning(f"Error iterating attachments: {e}")
            
            # Use HTML body if available, otherwise plain text
            email_body = body_html if body_html else body_text
            
            result = {
                'sender_name': sender_name or '',
                'sender_email': sender_email or '',
                'reply_to_email': reply_to or sender_email or '',
                'reply_to_name': reply_to_name or '',  # Name extracted from body if found
                'subject': subject,
                'body_text': body_text,
                'body_html': body_html,
                'email_body': email_body,
                'date': self._format_date(msg.date) if (hasattr(msg, 'date') and msg.date) else '',
                'attachments_info': attachments_info,
                # Note: We don't store the message object in the result as it's not serializable
                # We'll reopen the file when extracting attachments
            }
            
            msg.close()
            return result
            
        except Exception as e:
            logger.error(f"Error parsing email file: {str(e)}", exc_info=True)
            raise Exception(f"Failed to parse email: {str(e)}")
    
    def extract_attachments(self, save_directory: str) -> List[Dict]:
        """
        Extract and save attachments from the email
        
        Args:
            save_directory: Directory where attachments should be saved
            
        Returns:
            List of dicts with attachment info including saved paths
        """
        if not EXTRACT_MSG_AVAILABLE:
            raise ImportError("extract_msg library is required")
        
        os.makedirs(save_directory, exist_ok=True)
        saved_attachments = []
        
        try:
            msg = extract_msg.Message(self.msg_path)
            
            if hasattr(msg, 'attachments') and msg.attachments is not None:
                try:
                    for attachment in msg.attachments:
                        try:
                            # Get filename
                            original_filename = None
                            if hasattr(attachment, 'longFilename') and attachment.longFilename:
                                original_filename = str(attachment.longFilename)
                            elif hasattr(attachment, 'shortFilename') and attachment.shortFilename:
                                original_filename = str(attachment.shortFilename)
                            
                            if not original_filename:
                                original_filename = f"attachment_{len(saved_attachments)}"
                            
                            # Create safe filename and unique stored name
                            safe_filename = original_filename.replace('/', '_').replace('\\', '_').replace(':', '_')
                            stored_filename = f"{uuid.uuid4()}_{safe_filename}"
                            save_path = os.path.join(save_directory, stored_filename)
                            
                            # Save attachment
                            # Use attachment.data directly (most reliable method)
                            attachment_saved = False
                            
                            # Try using attachment.data property (recommended approach)
                            if hasattr(attachment, 'data'):
                                try:
                                    # Safely get the data - accessing the property might raise an error
                                    try:
                                        data = attachment.data
                                    except Exception as e:
                                        logger.warning(f"Error accessing attachment.data property: {e}")
                                        data = None
                                    
                                    if not data:
                                        continue
                                    
                                    # Handle different data types
                                    if isinstance(data, (bytes, bytearray)):
                                        # Data is already bytes
                                        with open(save_path, 'wb') as f:
                                            f.write(data)
                                        attachment_saved = True
                                    elif isinstance(data, str):
                                        # Data is a string, encode to bytes
                                        with open(save_path, 'wb') as f:
                                            f.write(data.encode('utf-8'))
                                        attachment_saved = True
                                    else:
                                        # Unknown type, try to convert to bytes
                                        logger.warning(f"Attachment data is unexpected type: {type(data)}")
                                        with open(save_path, 'wb') as f:
                                            f.write(str(data).encode('utf-8'))
                                        attachment_saved = True
                                except Exception as e:
                                    logger.warning(f"Error writing attachment data manually: {e}", exc_info=True)
                            
                            if attachment_saved and os.path.exists(save_path):
                                saved_attachments.append({
                                    'original_filename': original_filename,
                                    'stored_filename': stored_filename,
                                    'path': save_path,
                                    'size': os.path.getsize(save_path)
                                })
                                logger.info(f"Extracted attachment: {original_filename} -> {save_path}")
                            else:
                                logger.warning(f"Failed to save attachment: {original_filename}")
                                
                        except Exception as e:
                            logger.error(f"Error extracting attachment: {str(e)}", exc_info=True)
                            continue
                except Exception as e:
                    logger.error(f"Error iterating attachments: {str(e)}", exc_info=True)
            
            msg.close()
            return saved_attachments
            
        except Exception as e:
            logger.error(f"Error extracting attachments: {str(e)}", exc_info=True)
            raise Exception(f"Failed to extract attachments: {str(e)}")


