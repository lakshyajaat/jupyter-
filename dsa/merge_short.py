def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    
    # Split the array into two 
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    # Merge the sorted 
    return merge(left, right)

def merge(left, right):
    merged = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1

    # Adding
    merged.extend(left[i:])
    merged.extend(right[j:])
    
    return merged

arr = [50, 60, 80, 40, 30, 20, 10, 100]
sorted_arr = merge_sort(arr)
print("Sorted array:", sorted_arr)
