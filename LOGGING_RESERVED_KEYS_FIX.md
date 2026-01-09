# Logging Reserved Keys Error - Fixed

## ❌ Error Explanation

```
KeyError: "Attempt to overwrite 'message' in LogRecord"
```

### What This Means

**Python's `LogRecord` class has built-in reserved attributes** that cannot be overwritten when using the `extra` parameter in logging calls.

### Reserved LogRecord Attributes

These keys **CANNOT** be used in `extra`:

- `name` - Logger name
- `message` - Formatted log message
- `msg` - Original log message
- `levelname` - Log level name (INFO, ERROR, etc.)
- `filename` - Source filename
- `lineno` - Line number
- `module` - Module name
- `funcName` - Function name
- `created` - Creation timestamp
- `thread` - Thread ID
- `process` - Process ID
- `exc_info` - Exception info
- `stack_info` - Stack trace info
- `asctime` - Human-readable time
- And more...

### Why It Happens

When you use:
```python
logger.error("Error", extra={"message": "something"})
```

Python tries to set `record.message = "something"`, but `message` is already a built-in attribute that stores the formatted log message. Python prevents this to maintain data integrity.

---

## ✅ Fixes Applied

### Fix 1: Category Service (`app/modules/categories/service.py`)

**Before:**
```python
logger.info("Category created", extra={"category_id": category.id, "user_id": user_id, "name": name})
```

**After:**
```python
logger.info("Category created", extra={"category_id": category.id, "user_id": user_id, "category_name": name})
```

### Fix 2: Exception Handler (`app/core/exceptions.py`)

**Before:**
```python
logger.error(
    "API exception",
    extra={
        "path": request.url.path,
        "method": request.method,
        "status_code": exc.status_code,
        "message": exc.message,  # ❌ Conflicts with LogRecord.message
        "detail": exc.detail,
    },
)
```

**After:**
```python
logger.error(
    "API exception",
    extra={
        "path": request.url.path,
        "method": request.method,
        "status_code": exc.status_code,
        "error_message": exc.message,  # ✅ Changed to error_message
        "detail": exc.detail,
    },
)
```

---

## ✅ Best Practices

### Safe Keys for `extra`

Use descriptive, specific keys that don't conflict:

- ✅ `category_name` instead of `name`
- ✅ `error_message` instead of `message`
- ✅ `user_email` instead of `email`
- ✅ `transaction_id` instead of `id`
- ✅ `error_detail` instead of `detail` (if needed)

### Pattern

```python
# ✅ Good - Use specific, non-reserved keys
logger.info("Action", extra={
    "category_id": 1,
    "category_name": "Food",  # Specific, not reserved
    "error_message": "Something went wrong"  # Specific, not reserved
})

# ❌ Bad - Uses reserved keys
logger.info("Action", extra={
    "name": "Food",  # Conflicts with LogRecord.name
    "message": "Error"  # Conflicts with LogRecord.message
})
```

---

## 🔍 Complete List of Reserved Attributes

For reference, here are the main reserved LogRecord attributes:

| Attribute | Description | Conflict? |
|-----------|-------------|-----------|
| `name` | Logger name | ✅ Yes |
| `msg` | Original message | ✅ Yes |
| `message` | Formatted message | ✅ Yes |
| `levelname` | Log level name | ✅ Yes |
| `levelno` | Log level number | ✅ Yes |
| `pathname` | Full pathname | ✅ Yes |
| `filename` | Filename | ✅ Yes |
| `module` | Module name | ✅ Yes |
| `lineno` | Line number | ✅ Yes |
| `funcName` | Function name | ✅ Yes |
| `created` | Creation time | ✅ Yes |
| `msecs` | Milliseconds | ✅ Yes |
| `relativeCreated` | Relative time | ✅ Yes |
| `thread` | Thread ID | ✅ Yes |
| `threadName` | Thread name | ✅ Yes |
| `processName` | Process name | ✅ Yes |
| `process` | Process ID | ✅ Yes |
| `exc_info` | Exception info | ✅ Yes |
| `exc_text` | Exception text | ✅ Yes |
| `stack_info` | Stack info | ✅ Yes |
| `asctime` | Human-readable time | ✅ Yes |

---

## ✅ Status

**✅ FIXED** - Both logging conflicts are resolved:

1. ✅ Changed `"name"` → `"category_name"` in category service
2. ✅ Changed `"message"` → `"error_message"` in exception handler

All logging calls now work correctly without conflicts!

---

## 📝 Summary

**Problem:** Using reserved LogRecord attributes (`name`, `message`) in `extra` dictionary  
**Solution:** Changed to specific, non-reserved keys (`category_name`, `error_message`)  
**Status:** ✅ **FIXED**

The application logging now works correctly! 🚀

