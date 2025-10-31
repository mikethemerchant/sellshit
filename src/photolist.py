# generate_image_names.py

def generate_image_names(item_id, count):
    return [f"{item_id}_{i}.jpg" for i in range(1, count + 1)]

# Example usage
item_id = int(input("Enter item ID: "))
count = int(input("Enter image count: "))

names = generate_image_names(item_id, count)
print(", ".join(names))

