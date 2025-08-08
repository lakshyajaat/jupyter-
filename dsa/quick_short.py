def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[0]
    left = [x for x in arr[1:] if x <= pivot]
    right = [x for x in arr[1:] if x > pivot]
    return quick_sort(left) + [pivot] + quick_sort(right)

# Example usage
arr = [50, 60, 80, 40, 30, 20, 10, 100]
sorted_arr = quick_sort(arr)
print("Sorted array:", sorted_arr)
