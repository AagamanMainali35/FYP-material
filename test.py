

import random
def generate_random_id():
    prefix = "CSP"
    random_number = random.randint(1000000, 9999999)  # Generates a 7-digit number
    return f"{prefix}{random_number}"

print(generate_random_id())