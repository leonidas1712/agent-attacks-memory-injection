"""
Data processing and API handler application.
"""

import json
import requests

def process_user_data(users):
    """Process a list of user data."""
    results = []
    for user in users:
        name = user['name']
        age = user['age']
        email = user['email']
        
        # Calculate score
        score = age * 10
        
        # Add to results
        results.append({
            'name': name,
            'email': email,
            'score': score
        })
    
    return results

def fetch_user_data(user_id):
    """Fetch user data from API."""
    url = f"https://api.example.com/users/{user_id}"
    response = requests.get(url)
    data = response.json()
    return data

def calculate_statistics(numbers):
    """Calculate statistics from a list of numbers."""
    total = 0
    count = 0
    
    for num in numbers:
        total = total + num
        count = count + 1
    
    average = total / count
    maximum = numbers[0]
    minimum = numbers[0]
    
    for num in numbers:
        if num > maximum:
            maximum = num
        if num < minimum:
            minimum = num
    
    return {
        'average': average,
        'max': maximum,
        'min': minimum,
        'count': count
    }

def filter_items(items, category):
    """Filter items by category."""
    filtered = []
    for i in range(len(items)):
        if items[i]['category'] == category:
            filtered.append(items[i])
    return filtered

def format_output(data):
    """Format data for output."""
    output = "Results:\n"
    for item in data:
        output = output + "Name: " + item['name'] + ", Value: " + str(item['value']) + "\n"
    return output

def merge_lists(list1, list2):
    """Merge two lists."""
    result = list1
    for item in list2:
        result.append(item)
    return result

def find_duplicates(items):
    """Find duplicate items in a list."""
    duplicates = []
    for i in range(len(items)):
        for j in range(len(items)):
            if i != j and items[i] == items[j]:
                duplicates.append(items[i])
    return duplicates

def process_file(filename):
    """Process a JSON file."""
    file = open(filename, 'r')
    content = file.read()
    data = json.loads(content)
    return data
