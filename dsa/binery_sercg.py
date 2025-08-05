def binary_search(arr, target):
    low = 0
    high = len(arr) - 1

    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid  # `mid`
        elif arr[mid] < target:
            low = mid + 1  #right half
        else:
            high = mid - 1  #left half

    return -1  # not found


arr = [10, 20, 30, 40, 50, 60, 70, 80, 90]
target = 80

# Call binary search
index = binary_search(arr, target)

if index != -1:
    print(f"Element found at position {index}")
else:
    print("Element not found")
