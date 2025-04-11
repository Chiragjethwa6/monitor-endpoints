#!/usr/bin/env python3
import yaml
import requests
import time
import sys
import urllib.parse
from datetime import datetime
from collections import defaultdict

# Function to load configuration from the YAML file
def load_config(file_path):
    try:
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)
            # Validating that config is a list
            if not isinstance(config, list):
                raise ValueError("Configuration should be a list of endpoints")
            return config
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

# Function to extract domain from URL, ignoring port
def extract_domain(url):
    parsed_url = urllib.parse.urlparse(url)
    return parsed_url.netloc.split(':')[0]

# Function to perform health checks
def check_health(endpoint):
    url = endpoint['url']
    method = endpoint.get('method', 'GET')  # Defaulting to GET if method not specified
    headers = endpoint.get('headers', {})
    body_str = endpoint.get('body')
    
    # Parsing JSON body string into Python object if provided
    body = None
    if body_str:
        try:
            import json
            body = json.loads(body_str)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON body for {endpoint.get('name', url)}: {e}")
            return "DOWN", 0, f"Invalid JSON body: {e}"

    try:
        start_time = time.time()
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
    except requests.Timeout:
        return "DOWN", 0.5, "Timeout"
    except requests.RequestException as e:
        return "DOWN", 0, str(e)

# Main function to monitor endpoints
def monitor_endpoints(file_path):
    config = load_config(file_path)
    domain_stats = defaultdict(lambda: {"up": 0, "total": 0})
    
    # Setting the initial log time to now so we log immediately after first cycle
    last_log_time = time.time()
    
    try:
        while True:
            # Running a check cycle
            cycle_results = []
            for endpoint in config:
                domain = extract_domain(endpoint["url"])
                endpoint_name = endpoint.get("name", endpoint["url"])
                
                result = check_health(endpoint)
                status = result[0]
                response_time = result[1]
                
                # Updating statistics
                domain_stats[domain]["total"] += 1
                if status == "UP":
                    domain_stats[domain]["up"] += 1
                
                # Storing result for this cycle
                cycle_results.append({  
                    "name": endpoint_name,
                    "domain": domain, 
                    "status": status,
                    "response_time": response_time,
                    "details": result[2] if len(result) > 2 else None
                })
            
            # Logging results after each cycle completes
            current_time = time.time()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n--- {timestamp} ---")
            
            # Logging results by domain and availability
            for domain, stats in domain_stats.items():
                availability = round(100 * stats["up"] / stats["total"], 2)
                print(f"{domain} has {availability}% availability (UP: {stats['up']}, Total: {stats['total']})")
            
            # Logging details of current cycle  
            print("\nCurrent check cycle results:")
            for result in cycle_results:
                status_symbol = "✓" if result["status"] == "UP" else "✗"
                print(f"{status_symbol} {result['name']} - {result['response_time']:.3f}s", end="")
                if result["details"]:
                    print(f" - {result['details']}")
                else:
                    print()
            
            # Updating the last log time
            last_log_time = current_time
            
            # Waiting until 15 seconds have passed since the last log
            sleep_time = 15 - (time.time() - last_log_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")

# Entry point of the program
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <config_file_path>")
        sys.exit(1)

    config_file = sys.argv[1]

    # Validating that the config file is a YAML file
    if not (config_file.endswith('.yaml') or config_file.endswith('.yml')):
        print("Error: Configuration file must be a YAML file (.yaml or .yml)")
        sys.exit(1)
        
    try:
        monitor_endpoints(config_file)
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")