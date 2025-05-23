import pandas as pd
import matplotlib.pyplot as plt
from vizhelper.enhance import enhance_plot

# Dataset used: SampleSuperstore (https://www.kaggle.com/datasets/bravehart101/sample-supermarket-dataset)
data = pd.read_csv('data/SampleSuperstore.csv')
subcat_sales = data.groupby('Sub-Category')['Sales'].sum()
fig, ax = plt.subplots(figsize=(10, 6))
subcat_sales.plot(kind='bar', color='#e41a1c', ax=ax, rot=0)
ax.set_title('Sales by Sub-Category')

# Enhance
enhance_plot(
    ax,
    interactive=True,
    user_profile="visually_impaired",
    auto_label=True,
    auto_legend=True
)

plt.show()
