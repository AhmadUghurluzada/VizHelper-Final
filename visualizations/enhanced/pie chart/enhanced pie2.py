import pandas as pd
import matplotlib.pyplot as plt
from vizhelper.enhance import enhance_plot

# dataset used: https://www.kaggle.com/datasets/bravehart101/sample-supermarket-dataset 
data = pd.read_csv('data/SampleSuperstore.csv')
subcategory_sales = data.groupby('Sub-Category')['Sales'].sum()

fig, ax = plt.subplots(figsize=(7, 7))
ax.pie(subcategory_sales, labels=subcategory_sales.index, autopct='%1.1f%%', startangle=0, colors=plt.cm.tab20.colors)
ax.set_title('Sales Distribution by Sub-Category')
ax.axis('equal')

enhance_plot(
 ax,
 interactive=True,
 user_profile=None,
 auto_legend=False,
 auto_label=False,
 openai_api_key=None
)

plt.show()
