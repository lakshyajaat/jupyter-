# Node definition
class Node:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None

# Insert into BST
def insert(root, key):
    if root is None:
        return Node(key)
    if key < root.key:
        root.left = insert(root.left, key)
    else:
        root.right = insert(root.right, key)
    return root

# Traversals
def preorder(root, result):
    if root:
        result.append(root.key)
        preorder(root.left, result)
        preorder(root.right, result)

def inorder(root, result):
    if root:
        inorder(root.left, result)
        result.append(root.key)
        inorder(root.right, result)

def postorder(root, result):
    if root:
        postorder(root.left, result)
        postorder(root.right, result)
        result.append(root.key)


# --- Main program ---
# Take user input for keys
keys = list(map(int, input("Enter numbers to insert into BST (space-separated): ").split()))

root = None
for key in keys:
    root = insert(root, key)

# Ask for traversal choice
choice = input("Enter traversal type (preorder / inorder / postorder / all): ").lower()

if choice == "preorder":
    result = []
    preorder(root, result)
    print("Preorder:", result)

elif choice == "inorder":
    result = []
    inorder(root, result)
    print("Inorder:", result)

elif choice == "postorder":
    result = []
    postorder(root, result)
    print("Postorder:", result)

elif choice == "all":
    pre, ino, post = [], [], []
    preorder(root, pre)
    inorder(root, ino)
    postorder(root, post)
    print("Preorder:", pre)
    print("Inorder:", ino)
    print("Postorder:", post)

else:
    print("Invalid choice! Please enter preorder, inorder, postorder, or all.")
