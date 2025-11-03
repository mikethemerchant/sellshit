import pandas as pd

# Read the Excel file into a DataFrame
df = pd.read_excel('list.xlsx')

# Convert the DataFrame to a JSON string (using orient='records' for row-wise objects)
json_data = df.to_json(orient='records', indent=4)

# Save the JSON data to a file
with open('output.json', 'w') as f:
    f.write(json_data)

print("Conversion successful!")
