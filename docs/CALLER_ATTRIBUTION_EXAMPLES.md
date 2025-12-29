# Caller Attribution Examples

Comprehensive examples demonstrating arlogi's caller attribution feature using `from_`, `from_caller`, and `**{"from": depth}` parameters.

## Modern Setup

Before using caller attribution, ensure arlogi is configured using the `LoggingConfig` pattern:

```python
from arlogi import LoggingConfig, LoggerFactory, get_logger

# Configure arlogi
config = LoggingConfig(level="INFO")
LoggerFactory._apply_configuration(config)

# Get logger
logger = get_logger("example")
```

---

## Basic Caller Attribution

### Using `from_=0` (Current Function)

Shows the function where the log call is made:

```python
from arlogi import get_logger

logger = get_logger("example")

def process_data(data):
    # Shows [process_data()] - the current function
    logger.info("Processing data started", from_=0)

    result = data * 2

    # Shows [process_data()] - still the current function
    logger.info("Processing completed", from_=0, result=result)

    return result

process_data(42)
```

**Output:**

```text
INFO    [process_data()]                          Processing data started
INFO    [process_data()]                          Processing completed, result=84
```

### Using `from_=1` (Immediate Caller)

Shows the function that called the current function:

```python
from arlogi import get_logger

logger = get_logger("example")

def helper_function():
    # Shows [from main_function()] - the function that called helper_function
    logger.info("Helper operation completed", from_=1)
    logger.info("Helper operation details", from_=1, operation_type="compute")

def main_function():
    logger.info("Main started", from_=0)

    # This call will show main_function as the caller
    helper_function()

    logger.info("Main completed", from_=0)

main_function()
```

**Output:**

```text
INFO    [main_function()]                        Main started
INFO    [from main_function()]                   Helper operation completed
INFO    [from main_function()]                   Helper operation details, operation_type=compute
INFO    [main_function()]                        Main completed
```

### Using `from_=2` (Caller's Caller)

Shows the function that called the caller:

```python
from arlogi import get_logger

logger = get_logger("example")

def deep_function():
    # Shows [from top_function()] - two levels up the call stack
    logger.info("Deep operation", from_=2)
    logger.info("Deep details", from_=2, depth="deep")

def middle_function():
    logger.info("Middle function", from_=0)
    deep_function()

def top_function():
    logger.info("Top function", from_=0)
    middle_function()

top_function()
```

**Output:**

```text
INFO    [top_function()]                        Top function
INFO    [middle_function()]                      Middle function
INFO    [from top_function()]                   Deep operation
INFO    [from top_function()]                   Deep details, depth=deep
```

## Different Parameter Syntaxes

### `from_` Parameter (Recommended)

```python
from arlogi import get_logger

logger = get_logger("syntax_example")

def function_a():
    function_b()

def function_b():
    # Using from_= parameter
    logger.info("Using from_=0", from_=0)      # Shows [function_b()]
    logger.info("Using from_=1", from_=1)      # Shows [from function_a()]
    logger.info("Using from_=2", from_=2)      # Shows caller of function_a()

function_a()
```

### `from_caller` Parameter

```python
from arlogi import get_logger

logger = get_logger("syntax_example")

def function_a():
    function_b()

def function_b():
    # Using from_caller parameter
    logger.info("Using from_caller=0", from_caller=0)  # Shows [function_b()]
    logger.info("Using from_caller=1", from_caller=1)  # Shows [from function_a()]
    logger.info("Using from_caller=2", from_caller=2)  # Shows caller of function_a()

function_a()
```

### `from` Parameter with Dictionary Syntax

```python
from arlogi import get_logger

logger = get_logger("syntax_example")

def function_a():
    function_b()

def function_b():
    # Using from parameter with **dict syntax
    logger.info("Using **{'from': 0}", **{"from": 0})    # Shows [function_b()]
    logger.info("Using **{'from': 1}", **{"from": 1})    # Shows [from function_a()]
    logger.info("Using **{'from': 2}", **{"from": 2})    # Shows caller of function_a()

function_a()
```

## Parameter Precedence Examples

### Understanding Parameter Precedence

When multiple caller parameters are provided, arlogi follows this precedence:

1. `from` (highest)
2. `from_caller`
3. `from_` (lowest)

```python
from arlogi import get_logger

logger = get_logger("precedence_example")

def test_function():
    # from_ takes precedence over from_caller when both are present
    logger.info(
        "Mixed from_=0, from_caller=1",
        from_=0,           # This will be used (lower precedence)
        from_caller=1      # This will be ignored (higher precedence)
    )

    # from_caller takes precedence over from_
    logger.info(
        "Mixed from_=1, from_caller=0",
        from_=1,           # This will be ignored
        from_caller=0      # This will be used
    )

    # from (via dict) takes highest precedence
    logger.info(
        "All three parameters",
        **{"from": 2},    # This will be used (highest precedence)
        from_caller=1,    # This will be ignored
        from_=0           # This will be ignored
    )

test_function()
```

**Output:**

```text
INFO    [from test_function()]                   Mixed from_=0, from_caller=1
INFO    [test_function()]                        Mixed from_=1, from_caller=0
INFO    [from caller of test_function()]         All three parameters
```

## Cross-Module Attribution

### Same Module Attribution

```python
# file: app.py
from arlogi import get_logger

logger = get_logger("app")

def helper_function():
    # Shows [from main_function()] - same module, relative path
    logger.info("Helper completed", from_=1)

def main_function():
    logger.info("Main started", from_=0)
    helper_function()
    logger.info("Main completed", from_=0)

main_function()
```

**Output:**

```text
INFO    [main_function()]                        Main started
INFO    [from main_function()]                   Helper completed
INFO    [main_function()]                        Main completed
```

### Cross-Module Attribution

```python
# file: utils/helpers.py
from arlogi import get_logger

logger = get_logger("utils.helpers")

def process_data(data):
    # Shows [from app.main_function()] - different module, full path
    logger.info("Processing data", from_=1, data_id=data.get("id"))
    return {"status": "processed"}

# file: app/main.py
from utils.helpers import process_data
from arlogi import get_logger

logger = get_logger("app.main")

def main_function():
    logger.info("Starting main", from_=0)
    result = process_data({"id": 123, "content": "test"})
    logger.info("Main completed", from_=0, result=result)

main_function()
```

**Output:**

```text
INFO    [app.main_function()]                    Starting main
INFO    [from app.main_function()]               Processing data, data_id=123
INFO    [app.main_function()]                    Main completed, result={'status': 'processed'}
```

## Real-World Application Examples

### Web API Handler

```python
from arlogi import get_logger

logger = get_logger("api.handlers")

def handle_request(request):
    request_id = generate_request_id()

    logger.info(
        "Request received",
        from_=1,  # Shows the API endpoint that called this handler
        request_id=request_id,
        method=request.method,
        path=request.path
    )

    try:
        result = process_business_logic(request)

        logger.info(
            "Request processed successfully",
            from_=1,  # Still shows the API endpoint
            request_id=request_id,
            status_code=200
        )

        return result

    except Exception as e:
        logger.exception(
            "Request processing failed",
            from_=1,  # Shows the API endpoint
            request_id=request_id,
            error_type=type(e).__name__
        )
        raise

def user_endpoint(request):
    # The handler call above will show [from user_endpoint()]
    return handle_request(request)

def product_endpoint(request):
    # The handler call above will show [from product_endpoint()]
    return handle_request(request)
```

### Database Operations

```python
from arlogi import get_logger

logger = get_logger("database.operations")

def execute_query(query, params=None):
    start_time = time.time()

    # Show the business function that initiated the query
    logger.trace(
        "Executing query",
        from_=1,
        query=query,
        params=params
    )

    try:
        cursor = db.cursor()
        cursor.execute(query, params or [])
        result = cursor.fetchall()
        duration = (time.time() - start_time) * 1000

        # Show the business function for the result
        logger.debug(
            "Query completed",
            from_=1,
            query=query,
            duration_ms=round(duration, 2),
            rows_affected=len(result)
        )

        return result

    except Exception as e:
        duration = (time.time() - start_time) * 1000

        # Show the business function for the error
        logger.error(
            "Query failed",
            from_=1,
            query=query,
            duration_ms=round(duration, 2),
            error=str(e)
        )
        raise

def get_user_profile(user_id):
    logger.info("Fetching user profile", from_=1, user_id=user_id)

    query = "SELECT * FROM users WHERE id = %s"
    params = (user_id,)

    # execute_query will log this as [from get_user_profile()]
    return execute_query(query, params)

def authenticate_user(username, password):
    logger.info("Authenticating user", from_=1, username=username)

    query = "SELECT * FROM users WHERE username = %s AND password_hash = %s"
    params = (username, hash_password(password))

    # execute_query will log this as [from authenticate_user()]
    return execute_query(query, params)
```

### Background Job Processing

```python
from arlogi import get_logger

logger = get_logger("jobs.processor")

def process_job(job_data):
    job_id = job_data.get("id")
    job_type = job_data.get("type")

    # Show the job queue that dispatched this job
    logger.info(
        "Job processing started",
        from_=1,
        job_id=job_id,
        job_type=job_type
    )

    try:
        if job_type == "email":
            result = send_email_job(job_data)
        elif job_type == "report":
            result = generate_report_job(job_data)
        elif job_type == "cleanup":
            result = cleanup_job(job_data)
        else:
            raise ValueError(f"Unknown job type: {job_type}")

        # Show the job queue for completion
        logger.info(
            "Job processing completed",
            from_=1,
            job_id=job_id,
            result_status=result.get("status")
        )

        return result

    except Exception as e:
        # Show the job queue for failure
        logger.exception(
            "Job processing failed",
            from_=1,
            job_id=job_id,
            error_type=type(e).__name__
        )
        raise

def email_job_dispatcher():
    # process_job will show [from email_job_dispatcher()]
    process_job({
        "id": "job-123",
        "type": "email",
        "to": "user@example.com",
        "subject": "Welcome"
    })

def report_job_dispatcher():
    # process_job will show [from report_job_dispatcher()]
    process_job({
        "id": "job-456",
        "type": "report",
        "format": "pdf",
        "date_range": "2025-01-01:2025-12-31"
    })
```

### Class Method Attribution

```python
from arlogi import get_logger

logger = get_logger("services.user")

class UserService:
    def __init__(self):
        logger.info("UserService instance created", from_=0)

    def create_user(self, user_data):
        logger.info("Creating user", from_=1, email=user_data.get("email"))

        user_id = self._generate_user_id()
        self._save_user(user_id, user_data)
        self._send_welcome_email(user_data)

        logger.info("User created successfully", from_=1, user_id=user_id)
        return user_id

    def _generate_user_id(self):
        # Shows [from create_user()] - parent method
        logger.trace("Generating user ID", from_=1)
        return f"user_{uuid.uuid4().hex[:8]}"

    def _save_user(self, user_id, user_data):
        # Shows [from create_user()] - grandparent method
        logger.debug("Saving user to database", from_=2, user_id=user_id)
        # Database save logic here

    def _send_welcome_email(self, user_data):
        # Shows [from create_user()] - grandparent method
        logger.info("Sending welcome email", from_=2, email=user_data.get("email"))
        # Email sending logic here

# Usage
def application_logic():
    logger.info("Application started", from_=0)

    service = UserService()

    # create_user will show [from application_logic()]
    user_id = service.create_user({
        "email": "newuser@example.com",
        "name": "New User"
    })

    logger.info("Application completed", from_=0, user_id=user_id)
```

### Error Handling and Exception Tracking

```python
from arlogi import get_logger

logger = get_logger("error.tracking")

def risky_operation(data):
    logger.info("Starting risky operation", from_=1, data_id=data.get("id"))

    try:
        result = process_data(data)
        logger.info("Operation successful", from_=1, result=result)
        return result

    except ValueError as e:
        # Show the caller function for the error
        logger.warning(
            "Invalid data format",
            from_=1,
            error=str(e),
            data_type=type(data).__name__
        )
        raise

    except ConnectionError as e:
        # Show the caller function for connection error
        logger.error(
            "Network connection failed",
            from_=1,
            error=str(e),
            retry_possible=True
        )
        raise

    except Exception as e:
        # Show the caller function for unexpected errors
        logger.exception(
            "Unexpected error in operation",
            from_=1,
            error_type=type(e).__name__
        )
        raise

def business_process():
    try:
        # risky_operation will show [from business_process()]
        risky_operation({"id": 123, "value": "test"})
    except Exception:
        # business_process will be shown as the caller
        logger.error("Business process failed", from_=0)
        raise

def user_interface():
    try:
        # risky_operation will show [from user_interface()]
        risky_operation({"id": 456, "invalid": "data"})
    except Exception:
        # user_interface will be shown as the caller
        logger.error("UI operation failed", from_=0)
        raise
```

## Performance Considerations

### Efficient Caller Attribution

```python
from arlogi import get_logger

logger = get_logger("performance.example")

def high_frequency_function():
    # Standard logging without caller attribution (fast)
    for i in range(1000):
        logger.debug("Processing item %d", i)

    # Caller attribution only when needed
    logger.info("Batch processing started", from_=1, total=1000)

    for i in range(1000):
        # More expensive logging with caller attribution
        if i % 100 == 0:  # Log every 100th item
            logger.debug("Progress update", from_=1, progress=i)

def optimized_error_tracking():
    try:
        # Standard logging for normal operations
        logger.info("Normal operation")

        # Caller attribution only for debugging
        if DEBUG_MODE:
            logger.debug("Detailed debug info", from_=1, complex_data=data)

    except Exception as e:
        # Always use caller attribution for errors
        logger.exception("Error occurred", from_=1, error_type=type(e).__name__)
```

## Testing with Caller Attribution

### Unit Test Examples

```python
import pytest
from arlogi import get_logger

def test_function_call_attribution(caplog):
    logger = get_logger("test_module")

    def test_function():
        logger.info("Test message", from_=1)

    with caplog.at_level("INFO"):
        test_function()

        # Check that the log contains caller attribution
        assert "from test_function_call_attribution" in caplog.text

def test_deep_call_attribution(caplog):
    logger = get_logger("test_module")

    def deep_function():
        logger.info("Deep message", from_=2)

    def middle_function():
        deep_function()

    def top_function():
        middle_function()

    with caplog.at_level("INFO"):
        top_function()

        # Check that the log shows top_function as caller
        assert "from test_deep_call_attribution" in caplog.text

def test_parameter_precedence(caplog):
    logger = get_logger("test_module")

    with caplog.at_level("INFO"):
        # from_ should be used over from_caller
        logger.info("Test message", from_=1, from_caller=2)

        # Check that from_=1 was used
        assert "test_parameter_precedence" in caplog.text
```

## Best Practices

### Recommended Patterns

```python
from arlogi import get_logger

logger = get_logger("my_module")

# ✅ GOOD: Use from_=0 for function entry/exit
def my_function():
    logger.info("Function started", from_=0)
    # Function logic
    logger.info("Function completed", from_=0)

# ✅ GOOD: Use from_=1 to show business context
def helper_function():
    logger.info("Helper operation", from_=1, operation_type="compute")

# ✅ GOOD: Use caller attribution for errors
def risky_operation():
    try:
        # Operation logic
        pass
    except Exception as e:
        logger.exception("Operation failed", from_=1, error=str(e))
        raise

# ❌ AVOID: Overusing deep caller attribution
def deep_function():
    # from_=3+ is rarely useful and adds overhead
    logger.info("Deep operation", from_=3)

# ❌ AVOID: Mixing different caller parameters
def confusing_function():
    # This is confusing and should be avoided
    logger.info("Mixed message", from_=1, from_caller=2, **{"from": 3})
```

### Recommended Caller Attribution Depth

- `from_=0`: Function boundaries and state changes
- `from_=1`: Business operations and user actions
- `from_=2`: Rare cases for debugging complex call chains
- `from_=3+`: Generally avoid unless specific debugging needs

These examples demonstrate the power and flexibility of arlogi's caller attribution feature for creating maintainable, debuggable applications.
