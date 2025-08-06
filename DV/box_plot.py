    #irs dataset 
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

# Load the Iris dataset (built-in in seaborn)
iris = sns.load_dataset("iris")

# Optional: If you have a local CSV file, replace this line:
iris = pd.read_csv('/home/lakshya/jupyter/DV/iris.csv')  # Replace 'your_file.csv' with your actual file path

# ----------------------------
# 1. Box Plot
# ----------------------------
plt.figure(figsize=(8, 6))
sns.boxplot(x="species", y="sepal_length", data=iris)
plt.title("Box Plot of Sepal Length by Species")
plt.show()

# ----------------------------
# 2. Bar Plot (Mean Sepal Length per Species)
# ----------------------------
mean_sepal = iris.groupby("species")["sepal_length"].mean().reset_index()
plt.figure(figsize=(6, 4))
sns.barplot(x="species", y="sepal_length", data=mean_sepal)
plt.title("Bar Plot of Mean Sepal Length by Species")
plt.show()

# ----------------------------
# 3. Violin Plot
# ----------------------------
plt.figure(figsize=(8, 6))
sns.violinplot(x="species", y="sepal_length", data=iris)
plt.title("Violin Plot of Sepal Length by Species")
plt.show()
