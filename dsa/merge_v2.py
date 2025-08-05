def merge_sort(arr):
    # Base case: If the array has 0 or 1 element, it's sorted.
    if len(arr) <= 1:
        return arr
    
    # Split the array 
    mid = len(arr) // 2
    left_half = arr[:mid]   
    right_half = arr[mid:] 

    print(f"Splitting: {arr} → [Left: {left_half}] and [Right: {right_half}]")

    # Recursively sort each half
    left_sorted = merge_sort(left_half)
    right_sorted = merge_sort(right_half)

    # Merge the sorted
    merged_array = []
    
    print(f"Merging: Left = {left_sorted}, Right = {right_sorted}")

    i = j = 0

    # Compare elements from both 
    while i < len(left_sorted) and j < len(right_sorted):
        if left_sorted[i] <= right_sorted[j]:
            merged_array.append(left_sorted[i])
            i += 1
        else:
            merged_array.append(right_sorted[j])
            j += 1

    # Add any remaining elements from the left or right array
    merged_array.extend(left_sorted[i:])
    merged_array.extend(right_sorted[j:])

    print(f"Merged Result: {merged_array}")
    
    return merged_array

if __name__ == "__main__":
    arr = [50, 60, 80, 40, 30, 20, 10, 100]
    print("Original array:", arr)
    sorted_arr = merge_sort(arr)
    print("Sorted array:", sorted_arr)
