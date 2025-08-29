import pandas as pd
import random

# Generate synthetic dataset
num_records = 1000

# Sample names for random generation
first_names = ["Aditi", "Rahul", "Neha", "Arjun", "Kavita", "Manish", "Sneha", "Pooja", "Deepak", "Ramesh", "Lakshya", "Anjali", "Vikas", "Meera", "Rohan", "Priya", "Sanjay", "Simran", "Kunal", "Isha"]
streams = ["Engineering", "Arts", "Commerce", "Medical"]

data = []
for i in range(1, num_records+1):
    name = random.choice(first_names)
    score = random.randint(0, 100)
    stream = random.choice(streams)
    
    # Assign college based on score
    if score >= 90:
        college = "College A"
    elif score >= 75:
        college = "College B"
    elif score >= 60:
        college = "College C"
    elif score >= 40:
        college = "College D"
    else:
        college = "Not Eligible"
    
    data.append([i, name, score, stream, college])

# Create DataFrame
df = pd.DataFrame(data, columns=["Student_ID", "Name", "Score", "Stream", "College_Assigned"])

# Save to CSV
file_path = "/mnt/data/synthetic_college_dataset.csv"
df.to_csv(file_path, index=False)

file_path
