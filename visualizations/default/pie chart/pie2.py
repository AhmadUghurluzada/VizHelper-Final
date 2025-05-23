import pandas as pd
import matplotlib.pyplot as plt

# dataset used: https://www.kaggle.com/datasets/bravehart101/sample-supermarket-dataset 
data = pd.read_csv('data/SampleSuperstore.csv')

subcategory_sales = data.groupby('Sub-Category')['Sales'].sum()

plt.figure(figsize=(8, 8))
plt.pie(subcategory_sales, labels=subcategory_sales.index, autopct='%1.1f%%', startangle=90, colors=plt.cm.tab20.colors)
plt.title('Sales Distribution by Sub-Category')
plt.axis('equal')
plt.show()