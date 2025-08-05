arr = [10, 20, 30, 40, 50, 60, 70, 80, 90]

target = 60

for index, value in enumerate(arr):
    if value == target:
        print(f"Element found at position {index}")
        break
else:
    print("Element not found")
