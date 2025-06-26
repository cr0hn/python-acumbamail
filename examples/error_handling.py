#!/usr/bin/env python3
"""
Error Handling Example

This example demonstrates comprehensive error handling patterns and best practices
for the Acumbamail SDK, including retry logic, rate limiting, and graceful degradation.
"""

import os
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from functools import wraps
from acumbamail import (
    AcumbamailClient,
    AcumbamailError,
    AcumbamailRateLimitError,
    AcumbamailAPIError,
    AcumbamailValidationError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retry_on_exceptions: tuple = (AcumbamailAPIError, AcumbamailRateLimitError)
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retry_on_exceptions = retry_on_exceptions

def retry_with_backoff(config: RetryConfig):
    """Decorator for retrying operations with exponential backoff."""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except config.retry_on_exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_retries:
                        logger.error(f"Max retries ({config.max_retries}) exceeded for {func.__name__}")
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        config.base_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )
                    
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    time.sleep(delay)
                    
                except Exception as e:
                    # Don't retry on other exceptions
                    logger.error(f"Non-retryable error in {func.__name__}: {str(e)}")
                    raise
            
            # This should never be reached, but just in case
            raise last_exception
        
        return wrapper
    return decorator

class SafeAcumbamailClient:
    """Wrapper around AcumbamailClient with comprehensive error handling."""
    
    def __init__(self, client: AcumbamailClient, retry_config: Optional[RetryConfig] = None):
        self.client = client
        self.retry_config = retry_config or RetryConfig()
        self.error_counts = {
            'validation': 0,
            'rate_limit': 0,
            'api': 0,
            'other': 0
        }
    
    def _handle_error(self, error: Exception, operation: str) -> None:
        """Handle and log errors with appropriate categorization."""
        
        if isinstance(error, AcumbamailValidationError):
            self.error_counts['validation'] += 1
            logger.error(f"Validation error in {operation}: {str(error)}")
            
        elif isinstance(error, AcumbamailRateLimitError):
            self.error_counts['rate_limit'] += 1
            logger.warning(f"Rate limit exceeded in {operation}: {str(error)}")
            
        elif isinstance(error, AcumbamailAPIError):
            self.error_counts['api'] += 1
            logger.error(f"API error in {operation}: {str(error)}")
            
        else:
            self.error_counts['other'] += 1
            logger.error(f"Unexpected error in {operation}: {str(error)}")
    
    @retry_with_backoff(RetryConfig())
    def safe_get_lists(self) -> List[Any]:
        """Safely get lists with retry logic."""
        try:
            return self.client.get_lists()
        except Exception as e:
            self._handle_error(e, "get_lists")
            raise
    
    @retry_with_backoff(RetryConfig())
    def safe_create_list(self, name: str, description: str = "") -> Optional[Any]:
        """Safely create a list with validation and retry logic."""
        try:
            # Validate input
            if not name or not name.strip():
                raise AcumbamailValidationError("List name cannot be empty")
            
            if len(name) > 100:
                raise AcumbamailValidationError("List name too long (max 100 characters)")
            
            return self.client.create_list(name=name, description=description)
            
        except Exception as e:
            self._handle_error(e, "create_list")
            raise
    
    @retry_with_backoff(RetryConfig())
    def safe_add_subscriber(
        self,
        email: str,
        list_id: int,
        fields: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """Safely add a subscriber with validation and retry logic."""
        try:
            # Validate email
            if not email or '@' not in email:
                raise AcumbamailValidationError(f"Invalid email format: {email}")
            
            # Validate list_id
            if not isinstance(list_id, int) or list_id <= 0:
                raise AcumbamailValidationError(f"Invalid list_id: {list_id}")
            
            return self.client.add_subscriber(
                email=email,
                list_id=list_id,
                fields=fields or {}
            )
            
        except Exception as e:
            self._handle_error(e, "add_subscriber")
            raise
    
    @retry_with_backoff(RetryConfig())
    def safe_create_campaign(
        self,
        name: str,
        subject: str,
        content: str,
        list_ids: List[int],
        **kwargs
    ) -> Optional[Any]:
        """Safely create a campaign with validation and retry logic."""
        try:
            # Validate required fields
            if not name or not name.strip():
                raise AcumbamailValidationError("Campaign name cannot be empty")
            
            if not subject or not subject.strip():
                raise AcumbamailValidationError("Campaign subject cannot be empty")
            
            if not content or not content.strip():
                raise AcumbamailValidationError("Campaign content cannot be empty")
            
            if not list_ids or not isinstance(list_ids, list):
                raise AcumbamailValidationError("list_ids must be a non-empty list")
            
            if not all(isinstance(id_, int) and id_ > 0 for id_ in list_ids):
                raise AcumbamailValidationError("All list_ids must be positive integers")
            
            return self.client.create_campaign(
                name=name,
                subject=subject,
                content=content,
                list_ids=list_ids,
                **kwargs
            )
            
        except Exception as e:
            self._handle_error(e, "create_campaign")
            raise
    
    def get_error_summary(self) -> Dict[str, int]:
        """Get a summary of errors encountered."""
        return self.error_counts.copy()

def demonstrate_basic_error_handling():
    """Demonstrate basic error handling patterns."""
    
    print("🔧 BASIC ERROR HANDLING")
    print("=" * 60)
    
    client = AcumbamailClient(
        auth_token=os.getenv("ACUMBAMAIL_AUTH_TOKEN"),
        default_sender_name="Error Handling Example",
        default_sender_email="errors@example.com"
    )
    
    # Example 1: Handling specific exception types
    try:
        # This might fail if the token is invalid
        lists = client.get_lists()
        print(f"✅ Successfully retrieved {len(lists)} lists")
        
    except AcumbamailValidationError as e:
        print(f"❌ Validation error: {e}")
        
    except AcumbamailRateLimitError as e:
        print(f"⚠️  Rate limit exceeded: {e}")
        print("   Consider implementing exponential backoff")
        
    except AcumbamailAPIError as e:
        print(f"❌ API error: {e}")
        
    except AcumbamailError as e:
        print(f"❌ General Acumbamail error: {e}")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Example 2: Graceful degradation
    print("\n🔄 Graceful Degradation Example:")
    
    try:
        # Try to create a campaign
        campaign = client.create_campaign(
            name="Test Campaign",
            subject="Test Subject",
            content="<p>Test content</p>",
            list_ids=[123]  # This might not exist
        )
        print("✅ Campaign created successfully")
        
    except AcumbamailValidationError as e:
        print(f"❌ Campaign creation failed: {e}")
        print("   Using fallback strategy...")
        
        # Fallback: send single email instead
        try:
            email_id = client.send_single_email(
                to_email="test@example.com",
                subject="Fallback: Test Subject",
                content="<p>This is a fallback email</p>"
            )
            print(f"✅ Fallback single email sent (ID: {email_id})")
            
        except Exception as fallback_error:
            print(f"❌ Fallback also failed: {fallback_error}")

def demonstrate_retry_logic():
    """Demonstrate retry logic with exponential backoff."""
    
    print("\n🔄 RETRY LOGIC WITH EXPONENTIAL BACKOFF")
    print("=" * 60)
    
    client = AcumbamailClient(
        auth_token=os.getenv("ACUMBAMAIL_AUTH_TOKEN"),
        default_sender_name="Retry Example",
        default_sender_email="retry@example.com"
    )
    
    safe_client = SafeAcumbamailClient(client)
    
    # Example: Retry with exponential backoff
    try:
        lists = safe_client.safe_get_lists()
        print(f"✅ Retrieved {len(lists)} lists after retries")
        
    except Exception as e:
        print(f"❌ Failed after all retries: {e}")
    
    # Example: Safe campaign creation with validation
    try:
        campaign = safe_client.safe_create_campaign(
            name="Retry Test Campaign",
            subject="Testing retry logic",
            content="<p>This campaign tests retry logic</p>",
            list_ids=[1]  # Assuming this list exists
        )
        print(f"✅ Campaign created: {campaign.name}")
        
    except Exception as e:
        print(f"❌ Campaign creation failed: {e}")

def demonstrate_bulk_operations_with_error_handling():
    """Demonstrate error handling in bulk operations."""
    
    print("\n📦 BULK OPERATIONS WITH ERROR HANDLING")
    print("=" * 60)
    
    client = AcumbamailClient(
        auth_token=os.getenv("ACUMBAMAIL_AUTH_TOKEN"),
        default_sender_name="Bulk Error Example",
        default_sender_email="bulk@example.com"
    )
    
    safe_client = SafeAcumbamailClient(client)
    
    # Get or create a test list
    try:
        lists = safe_client.safe_get_lists()
        if lists:
            test_list = lists[0]
        else:
            test_list = safe_client.safe_create_list("Error Handling Test List")
        
        print(f"✅ Using list: {test_list.name}")
        
    except Exception as e:
        print(f"❌ Failed to setup test list: {e}")
        return
    
    # Bulk add subscribers with error handling
    subscribers_data = [
        ("valid@example.com", {"name": "Valid User"}),
        ("invalid-email", {"name": "Invalid User"}),  # This will fail
        ("another@example.com", {"name": "Another User"}),
        ("", {"name": "Empty Email"}),  # This will fail
        ("test@example.com", {"name": "Test User"})
    ]
    
    successful = 0
    failed = 0
    errors = []
    
    print(f"\n📧 Adding {len(subscribers_data)} subscribers...")
    
    for i, (email, fields) in enumerate(subscribers_data, 1):
        try:
            subscriber = safe_client.safe_add_subscriber(
                email=email,
                list_id=test_list.id,
                fields=fields
            )
            print(f"✅ {i:2d}. Added: {email}")
            successful += 1
            
        except AcumbamailValidationError as e:
            print(f"❌ {i:2d}. Validation failed: {email} - {str(e)}")
            failed += 1
            errors.append(f"Validation: {email} - {str(e)}")
            
        except AcumbamailRateLimitError as e:
            print(f"⚠️  {i:2d}. Rate limited: {email} - {str(e)}")
            failed += 1
            errors.append(f"Rate limit: {email} - {str(e)}")
            # Wait before continuing
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ {i:2d}. Unexpected error: {email} - {str(e)}")
            failed += 1
            errors.append(f"Unexpected: {email} - {str(e)}")
    
    print(f"\n📊 Bulk Operation Results:")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(successful / len(subscribers_data) * 100):.1f}%")
    
    # Show error summary
    error_summary = safe_client.get_error_summary()
    print(f"\n📋 Error Summary:")
    for error_type, count in error_summary.items():
        if count > 0:
            print(f"  {error_type}: {count}")

def demonstrate_circuit_breaker_pattern():
    """Demonstrate a simple circuit breaker pattern."""
    
    print("\n⚡ CIRCUIT BREAKER PATTERN")
    print("=" * 60)
    
    class CircuitBreaker:
        def __init__(self, failure_threshold: int = 5, timeout: int = 60):
            self.failure_threshold = failure_threshold
            self.timeout = timeout
            self.failure_count = 0
            self.last_failure_time = None
            self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
        def call(self, func, *args, **kwargs):
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.timeout:
                    self.state = "HALF_OPEN"
                    print("🔄 Circuit breaker: HALF_OPEN - testing connection")
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    print("✅ Circuit breaker: CLOSED - connection restored")
                return result
                
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    print(f"🚨 Circuit breaker: OPEN - too many failures ({self.failure_count})")
                
                raise
    
    # Create circuit breaker
    circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=30)
    
    client = AcumbamailClient(
        auth_token=os.getenv("ACUMBAMAIL_AUTH_TOKEN"),
        default_sender_name="Circuit Breaker Example",
        default_sender_email="circuit@example.com"
    )
    
    # Test circuit breaker with API calls
    for i in range(5):
        try:
            print(f"\n🔄 Attempt {i + 1}:")
            lists = circuit_breaker.call(client.get_lists)
            print(f"✅ Success: Retrieved {len(lists)} lists")
            
        except Exception as e:
            print(f"❌ Failed: {str(e)}")
            time.sleep(1)  # Brief pause between attempts

def main():
    """Main function to demonstrate error handling patterns."""
    
    print("🛡️  ERROR HANDLING PATTERNS")
    print("=" * 60)
    
    try:
        # Demonstrate different error handling patterns
        demonstrate_basic_error_handling()
        demonstrate_retry_logic()
        demonstrate_bulk_operations_with_error_handling()
        demonstrate_circuit_breaker_pattern()
        
        print(f"\n{'='*60}")
        print("✅ Error Handling Examples Completed")
        print("=" * 60)
        print("Key takeaways:")
        print("• Always handle specific exception types")
        print("• Implement retry logic with exponential backoff")
        print("• Use graceful degradation for critical operations")
        print("• Monitor and log errors appropriately")
        print("• Consider circuit breaker patterns for external APIs")
        
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main() 