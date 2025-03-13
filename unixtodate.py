from datetime import datetime

def unix_to_datetime(unix_timestamp):
    """
    Converts a Unix timestamp to a datetime object.
    
    Args:
        unix_timestamp (int): The Unix timestamp in seconds. 

    Returns:
        datetime: The corresponding datetime object. 
    """
    return datetime.fromtimestamp(unix_timestamp) 

# Example usage
unix_time = 1683574400  # Example Unix timestamp
datetime_obj = unix_to_datetime(unix_time) 
print(datetime_obj)  # Output: 2023-05-08 18:00:00