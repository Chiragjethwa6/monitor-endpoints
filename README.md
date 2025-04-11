# Endpoint Availability Monitor

An endpoint monitoring tool that tracks and reports the availability of HTTP/HTTPS endpoints as specified in a YAML configuration file.

## Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package manager)

### Requirements

The following dependencies are required:

```
pyyaml>=6.0
requests>=2.28.0
```

### Setup

1. Clone this repository:
   ```bash
   git clone git@github.com:Chiragjethwa6/monitor-endpoints.git
   cd monitor-endpoints
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Create a YAML configuration file following the format below.
2. Run the monitor with the path to your configuration file:
   ```bash
   python main.py <path-to-config-file.yaml>
   ```
3. To stop monitoring, press `Ctrl+C`.

### YAML Configuration Format

```yaml
- body: '{"foo":"bar"}'
  headers:
    content-type: application/json
  method: POST
  name: sample body up
  url: https://example.com/body
- name: sample index up
  url: https://example.com/
- body: "{}"
  headers:
    content-type: application/json
  method: POST
  name: sample body down
  url: https://example.com/body
- name: sample error down
  url: https://example.com/error
```

### Configuration Parameters

- **name** (string, required) — A free-text name to describe the HTTP endpoint.
- **url** (string, required) — The URL of the HTTP endpoint.
  - You may assume that the URL is always a valid HTTP or HTTPS address.
- **method** (string, optional) — The HTTP method of the endpoint.
  - If this field is present, you may assume it's a valid HTTP method (e.g. GET, POST, etc.).
  - If this field is omitted, the default is GET.
- **headers** (dictionary, optional) — The HTTP headers to include in the request.
  - If this field is present, you may assume that the keys and values of this dictionary are strings that are valid HTTP header names and values.
  - If this field is omitted, no headers need to be added to or modified in the HTTP request.
- **body** (string, optional) — The HTTP body to include in the request.
  - If this field is present, you should assume it's a valid JSON-encoded string. You do not need to account for non-JSON request bodies.
  - If this field is omitted, no body is sent in the request.

## Issues Identified and Changes Made

### 1. Response Time Monitoring

**Issue**: Original code didn't check if endpoints responded within 500ms, only checking status codes.

**Changes Made**: 
- Added timeout parameter to requests and measured response time
- Used both status code and response time to determine availability

```python
response = requests.request(
    method, 
    url, 
    headers=headers, 
    json=body,
    timeout=0.5  # 500ms timeout as per requirements
)
response_time = time.time() - start_time

# Checking both status code and response time for availability
if 200 <= response.status_code < 300 and response_time <= 0.5:
    return "UP", response_time
else:
    reason = "Status code out of range" if response.status_code < 200 or response.status_code >= 300 else "Response too slow"
    return "DOWN", response_time, reason
```

### 2. Domain Calculation

**Issue**: Original domain extraction didn't properly ignore port numbers.

**Changes Made**:
- Implemented proper domain extraction using urllib.parse
- Explicitly removed port numbers from domain calculation

```python
def extract_domain(url):
    parsed_url = urllib.parse.urlparse(url)
    return parsed_url.netloc.split(':')[0]
```

### 3. Default HTTP Method

**Issue**: Original code didn't set a default method when not specified in configuration.

**Changes Made**:
- Added 'GET' as the default value for the method parameter

```python
method = endpoint.get('method', 'GET')  # Defaulting to GET if method not specified
```

### 4. YAML File Validation

**Issue**: Original code had no validation that the command line argument is a YAML file.

**Changes Made**:
- Added validation to check if the file has a .yaml or .yml extension

```python
# Validating that the config file is a YAML file
if not (config_file.endswith('.yaml') or config_file.endswith('.yml')):
    print("Error: Configuration file must be a YAML file (.yaml or .yml)")
    sys.exit(1)
```

### 5. JSON Body Processing

**Issue**: Original code didn't properly handle JSON body strings.

**Changes Made**:
- Added proper JSON parsing for the body parameter
- Added error handling for invalid JSON

```python
# Parsing JSON body string into Python object if provided
body = None
if body_str:
    try:
        import json
        body = json.loads(body_str)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON body for {endpoint.get('name', url)}: {e}")
        return "DOWN", 0, f"Invalid JSON body: {e}"
```

### 6. Logging Improvements

**Issue**: Original code logged results after all checks and waited 15 seconds, which could cause irregular logging intervals for slow responses.

**Changes Made**:
- Improved time-based logging mechanism
- Added timestamp to log output
- Enhanced logging with more detailed information
- Added formatting for better readability

```python
# Logging results after each cycle completes
current_time = time.time()
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(f"\n--- {timestamp} ---")

# Logging results by domain and availability
for domain, stats in domain_stats.items():
    availability = round(100 * stats["up"] / stats["total"], 2)
    print(f"{domain} has {availability}% availability (UP: {stats['up']}, Total: {stats['total']})")

# Waiting until 15 seconds have passed since the last log
sleep_time = 15 - (time.time() - last_log_time)
if sleep_time > 0:
    time.sleep(sleep_time)
```

### 7. Enhanced Error Handling

**Issue**: Original code had limited error handling for requests and configuration issues.

**Changes Made**:
- Added comprehensive error handling for requests
- Added validation for the configuration file
- Improved error reporting for better troubleshooting

```python
try:
except requests.Timeout:
    return "DOWN", 0.5, "Timeout"
except requests.RequestException as e:
    return "DOWN", 0, str(e)
```

## Sample Output

```
--- 2025-04-11 13:04:45 ---
example.com has 50.0% availability (UP: 4, Total: 8)

Current check cycle results:
✓ sample body up - 0.320s
✓ sample index up - 0.131s
✗ sample body down - 0.165s - Status code out of range
✗ sample error down - 0.500s - Timeout
```