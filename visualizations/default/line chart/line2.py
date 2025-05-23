import pandas as pd
import matplotlib.pyplot as plt

# dataset used: https://www.kaggle.com/datasets/mohammadtalib786/retail-sales-dataset
data = pd.read_csv('data/retail_sales_dataset.csv')

data['Date'] = pd.to_datetime(data['Date'])

daily_sales = data.groupby('Date')['Total Amount'].sum()

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(daily_sales.index, daily_sales, marker='o', color='grey')
ax.set_title('Daily Total Sales for One Year')

plt.show()
