import pandas as pd
import matplotlib.pyplot as plt
from vizhelper.enhance import enhance_plot

# dataset used: https://www.kaggle.com/datasets/bhadramohit/customer-shopping-latest-trends-dataset 
data = pd.read_csv('data/shopping_trends_updated.csv')

data['Purchase Amount (USD)'] = pd.to_numeric(data['Purchase Amount (USD)'], errors='coerce')

fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(data['Age'], data['Purchase Amount (USD)'], color='darkorange', alpha=0.7)
ax.set_title('Purchase Amount vs Age')

enhance_plot(
    ax,
    interactive=True,
    user_profile=None,
    auto_legend=True,  
    auto_label=True,   
    openai_api_key=None
)

plt.show()

