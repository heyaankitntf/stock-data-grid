---
name: streamlit-expert
description: Expert knowledge for building stable, performant Streamlit applications
---

# Streamlit Expert Skill

Comprehensive guide for building production-ready Streamlit apps with focus on stability, performance, and user experience.

## Core Principles

### 1. State Management
- **Always initialize session state** before using it
- Use `st.session_state.setdefault(key, default_value)` pattern
- Never rely on widget state between reruns
- Clear unnecessary state to prevent memory leaks

### 2. Layout Stability (Prevent FOUC/Layout Shifts)

**Problem:** Elements "dance" or shift on page refresh/rerun
**Root Cause:** CSS loads after HTML, conditional rendering changes layout height

**Solutions:**

```python
# ❌ BAD: Conditional rendering without space reservation
if condition:
    st.button("Action")  # Button appears/disappears

# ✅ GOOD: Always render, disable when needed
st.button("Action", disabled=not condition)

# ✅ GOOD: Reserve space with placeholder
if condition:
    st.button("Action")
else:
    st.markdown('<div style="min-height:44px"></div>', unsafe_allow_html=True)
```

**CSS Fixes:**
```css
/* Disable default animations */
.element-container {
    animation: none !important;
    transition: none !important;
}

/* Reserve minimum heights */
.stButton { min-height: 44px; }
[data-testid="stVerticalBlock"] { min-height: 100px; }

/* Fast fade-in only */
@keyframes fadeIn {
    from { opacity: 0.98; }
    to { opacity: 1; }
}
[data-testid="stAppViewContainer"] {
    animation: fadeIn 0.1s ease-in;
}

/* Prevent scrollbar shift */
body { overflow-y: scroll; }
```

### 3. Performance Optimization

**Caching:**
```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def expensive_computation(params):
    return result

@st.cache_resource  # Singleton resources (DB connections, ML models)
def get_database():
    return db_connection
```

**Parallel Processing:**
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_items(items):
    results = []
    with ThreadPoolExecutor(max_workers=min(10, len(items))) as executor:
        futures = {executor.submit(process_one, item): item for item in items}
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logging.error(f"Error: {e}")
    return results
```

**Conditional Reruns:**
```python
# Only rerun when necessary
if st.button("Update"):
    # Do work
    st.rerun()  # Explicit rerun

# Use fragments for isolated reruns (Streamlit 1.33+)
@st.experimental_fragment
def update_section():
    st.button("Refresh only this section")
```

### 4. Progress Indicators

**Thread-Safe Progress:**
```python
def long_task(items, pbar, status):
    total = len(items)
    for i, item in enumerate(items):
        try:
            status.caption(f"Processing {i+1}/{total}...")
            pbar.progress((i+1) / total)
        except Exception:
            pass  # Continue even if UI update fails
```

### 5. Configuration Best Practices

**`.streamlit/config.toml`:**
```toml
[runner]
fastReruns = true

[client]
showErrorDetails = false
toolbarMode = "minimal"

[server]
enableXsrfProtection = true
maxUploadSize = 200

[browser]
gatherUsageStats = false
```

### 6. Common Issues & Solutions

#### Issue: "Dancing" Elements on Refresh
**Solution:**
- Remove conditional rendering
- Add CSS to disable animations
- Use placeholders for dynamic content
- Set `fastReruns = true` in config

#### Issue: Slow App Performance
**Solution:**
- Use `@st.cache_data` for expensive computations
- Implement pagination for large datasets
- Use `st.experimental_fragment` for partial updates
- Minimize reruns with `st.form`

#### Issue: Memory Leaks
**Solution:**
```python
# Clear unused session state
def cleanup_session():
    keys_to_remove = [k for k in st.session_state if k.startswith('temp_')]
    for k in keys_to_remove:
        del st.session_state[k]
```

#### Issue: Widget State Lost on Rerun
**Solution:**
```python
# Store in session state immediately
if 'counter' not in st.session_state:
    st.session_state.counter = 0

if st.button("Increment"):
    st.session_state.counter += 1
    st.rerun()
```

### 7. Authentication Patterns

**File-Based Session:**
```python
def save_session(token, expiry_days=30):
    from datetime import timedelta
    expiry = (datetime.now() + timedelta(days=expiry_days)).isoformat()
    SESSION_FILE.write_text(json.dumps({"token": token, "expiry": expiry}))

def check_auth():
    if not SESSION_FILE.exists():
        return False
    data = json.loads(SESSION_FILE.read_text())
    expiry = datetime.fromisoformat(data["expiry"])
    return datetime.now() < expiry
```

### 8. Data Display Best Practices

**DataFrames:**
```python
# Use styling for better UX
styled = df.style\
    .background_gradient(subset=['value'], cmap='RdYlGn')\
    .format({'price': '${:.2f}', 'change': '{:+.2%}'})\
    .hide(axis='index')

st.dataframe(styled, use_container_width=True, height=400)
```

**Metrics:**
```python
col1, col2, col3 = st.columns(3)
col1.metric("Revenue", "$12.5M", delta="+15%")
col2.metric("Users", "1.2K", delta="-5%", delta_color="inverse")
col3.metric("Growth", "23%", delta="2%")
```

### 9. Forms for Batch Input

```python
with st.form("my_form"):
    name = st.text_input("Name")
    age = st.number_input("Age")
    submitted = st.form_submit_button("Submit")

if submitted:
    # Process all inputs together, single rerun
    st.write(f"Hello {name}, age {age}")
```

### 10. Error Handling

```python
try:
    risky_operation()
except Exception as e:
    st.error(f"❌ Error: {str(e)}", icon="🚫")
    logging.error(f"Error details: {e}", exc_info=True)
```

## Testing & Debugging

**Check Performance:**
```python
import time
start = time.time()
expensive_function()
st.caption(f"Took {time.time() - start:.2f}s")
```

**Debug Session State:**
```python
with st.expander("🐛 Debug: Session State"):
    st.write(st.session_state)
```

## Production Checklist

- [ ] All expensive operations cached
- [ ] Error handling on all external calls
- [ ] Session state properly initialized
- [ ] No conditional rendering causing layout shifts
- [ ] Progress indicators for long operations
- [ ] Proper logging configured
- [ ] Config.toml optimized
- [ ] Memory cleanup implemented
- [ ] Mobile-responsive CSS
- [ ] Security: XSS protection, input validation

## Resources

- **Docs:** https://docs.streamlit.io
- **Forum:** https://discuss.streamlit.io
- **Gallery:** https://streamlit.io/gallery
- **Best Practices:** https://blog.streamlit.io/common-app-problems-resource-limits/
