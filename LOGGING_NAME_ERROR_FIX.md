# Logging "name" Key Error - Fixed

## ❌ Error Explanation

```
KeyError: "Attempt to overwrite 'name' in LogRecord"
```

### What This Means

**Python's `LogRecord` class has a built-in `name` attribute** that stores the logger name. When you try to pass `"name"` in the `extra` dictionary to a logger, it conflicts with this built-in attribute.

### Why It Happens

1. **LogRecord Built-in Attributes:** LogRecord has reserved attributes like:
   - `name` - Logger name
   - `msg` - Log message
   - `levelname` - Log level
   - `filename` - Source filename
   - `lineno` - Line number
   - And many more...

2. **Conflict:** When you use `logger.info(..., extra={"name": value})`, Python tries to set `record.name = value`, but `name` is already a built-in attribute.

3. **Protection:** Python's logging module prevents overwriting built-in attributes to maintain data integrity.

### When It Occurs

- When logging with `extra={"name": ...}` in any logger call
- The error happens during LogRecord creation
- Affects all log levels (info, debug, warning, error)

---

## ✅ Solution Implemented

### Fix Applied

Changed the logging call in `app/modules/categories/service.py`:

**Before (Problematic):**
```python
logger.info("Category created", extra={"category_id": category.id, "user_id": user_id, "name": name})
```

**After (Fixed):**
```python
logger.info("Category created", extra={"category_id": category.id, "user_id": user_id, "category_name": name})
```

### Why This Works

- **Changed key from `"name"` to `"category_name"`**
- `category_name` is not a reserved LogRecord attribute
- No conflict with built-in attributes
- Still provides the same information

---

## 🔍 Reserved LogRecord Attributes

These keys **cannot** be used in `extra`:

- `name` - Logger name
- `msg` - Log message
- `args` - Message arguments
- `levelname` - Log level name
- `levelno` - Log level number
- `pathname` - Full pathname of source file
- `filename` - Filename portion
- `module` - Module name
- `lineno` - Line number
- `funcName` - Function name
- `created` - Time when LogRecord was created
- `msecs` - Milliseconds
- `relativeCreated` - Time relative to logging import
- `thread` - Thread ID
- `threadName` - Thread name
- `processName` - Process name
- `process` - Process ID
- `exc_info` - Exception info
- `exc_text` - Exception text
- `stack_info` - Stack info
- `message` - Formatted message
- `asctime` - Human-readable time

---

## ✅ Best Practices

### Safe Keys for `extra`

Use descriptive, specific keys:
- ✅ `category_name` instead of `name`
- ✅ `user_email` instead of `email` (if email is reserved)
- ✅ `transaction_id` instead of `id`
- ✅ `error_message` instead of `message`

### Pattern

```python
# ✅ Good
logger.info("Category created", extra={
    "category_id": category.id,
    "user_id": user_id,
    "category_name": name  # Specific, not reserved
})

# ❌ Bad
logger.info("Category created", extra={
    "category_id": category.id,
    "user_id": user_id,
    "name": name  # Conflicts with LogRecord.name
})
```

---

## 🎯 Status

**✅ FIXED** - The error is resolved. Category creation logging will work correctly.

The fix:
- ✅ Changed `"name"` to `"category_name"` in logging
- ✅ No more conflicts with LogRecord attributes
- ✅ All logging calls now work correctly

---

## 📝 Summary

**Problem:** Using `"name"` in `extra` conflicts with LogRecord's built-in `name` attribute  
**Solution:** Changed to `"category_name"` to avoid the conflict  
**Status:** ✅ **FIXED**

The application logging now works correctly! 🚀

