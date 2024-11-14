import random
from typing import List, Tuple, Dict
from collections import defaultdict
import csv

def parse_history(history_data: str) -> Dict[str, List[str]]:
    """Parse the gift exchange history and return a dict of giver -> [recipients]"""
    lines = history_data.strip().split('\n')[1:]  # Skip header
    history = defaultdict(list)
    people = set()
    
    for line in lines:
        giver, recipient, year = line.split(', ')
        history[giver].append(recipient)
        people.add(giver)
        people.add(recipient)
    
    return dict(history), list(people)

def is_valid_assignment(giver: str, recipient: str, history: Dict[str, List[str]]) -> bool:
    """Check if an assignment is valid based on the rules"""
    if giver == recipient:  # Can't give to yourself
        return False
    
    # Can't give to same person as last 2 years
    recent_recipients = history.get(giver, [])[-2:]  # Get last 2 recipients
    return recipient not in recent_recipients

def generate_assignments(history: Dict[str, List[str]], people: List[str], max_attempts: int = 1000) -> List[Tuple[str, str]]:
    """Generate valid gift exchange assignments"""
    for attempt in range(max_attempts):
        assignments = []
        available_recipients = people.copy()
        temp_people = people.copy()
        random.shuffle(temp_people)
        
        success = True
        for giver in temp_people:
            valid_recipients = [r for r in available_recipients 
                              if is_valid_assignment(giver, r, history)]
            
            if not valid_recipients:
                success = False
                break
                
            recipient = random.choice(valid_recipients)
            assignments.append((giver, recipient))
            available_recipients.remove(recipient)
        
        if success:
            return assignments
            
    raise Exception("Could not find valid assignments after maximum attempts")

# Read historical data from CSV file
def read_history_from_csv(file_path: str) -> str:
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        return "\n".join([", ".join(row) for row in reader])

# Load historical data
history_data = read_history_from_csv('history_data.csv')

# Generate new assignments
history, people = parse_history(history_data)
assignments = generate_assignments(history, people)

# Print results
print("\nNew Gift Exchange Assignments:")
for giver, recipient in sorted(assignments):
    print(f"{giver} → {recipient}")

