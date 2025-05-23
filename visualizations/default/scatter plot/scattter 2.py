import pandas as pd
import matplotlib.pyplot as plt

# dataset used: https://www.kaggle.com/datasets/bhadramohit/customer-shopping-latest-trends-dataset 
data = pd.read_csv('data/shopping_trends_updated.csv')

data['Purchase Amount (USD)'] = pd.to_numeric(data['Purchase Amount (USD)'], errors='coerce')

plt.figure(figsize=(8, 6))
plt.scatter(data['Age'], data['Purchase Amount (USD)'], color='darkorange', alpha=0.7)
plt.title('Purchase Amount vs Age of All Patients')
plt.show()
