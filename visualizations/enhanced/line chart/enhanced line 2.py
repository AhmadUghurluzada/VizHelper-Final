import pandas as pd
import matplotlib.pyplot as plt
from vizhelper.enhance import enhance_plot

# dataset used: https://www.kaggle.com/datasets/mohammadtalib786/retail-sales-dataset
data = pd.read_csv('data/retail_sales_dataset.csv')

data['Date'] = pd.to_datetime(data['Date'])

daily_sales = data.groupby('Date')['Total Amount'].sum()

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(daily_sales.index, daily_sales, marker='o', color='grey')
ax.set_title('Daily Total Sales for One Year')

enhance_plot(
    ax,
    interactive=True,
    user_profile="colorblind",
    auto_legend=True,
    auto_label=True,
    openai_api_key="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"
)

plt.show()
