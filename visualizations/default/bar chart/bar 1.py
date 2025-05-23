import pandas as pd
import matplotlib.pyplot as plt

# Dataset used: SampleSuperstore (https://www.kaggle.com/datasets/bravehart101/sample-supermarket-dataset)
data = pd.read_csv('data/SampleSuperstore.csv')
category_sales = data.groupby('Category')['Sales'].sum()

fig, ax = plt.subplots(figsize=(8, 6))
category_sales.plot(kind='bar', color='skyblue', ax=ax, rot=0)
ax.set_title('Sales by Category')
plt.show()
