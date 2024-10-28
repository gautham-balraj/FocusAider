from datetime import datetime

def get_current_time_and_date():
    # Get current date and time
    now = datetime.now()
    
    # Format date and time as a string
    current_time_and_date = now.strftime("%Y-%m-%d %H:%M:%S")
    
    return current_time_and_date