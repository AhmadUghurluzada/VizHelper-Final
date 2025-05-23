import pandas as pd
import matplotlib.pyplot as plt

# Dataset used: https://www.kaggle.com/datasets/jahnavipaliwal/customer-feedback-and-satisfaction 
data = pd.read_csv('data/customer_feedback_satisfaction.csv')

loyalty_counts = data['LoyaltyLevel'].value_counts()
custom_colors = ["skyblue", "lightgreen", "salmon", "plum"]

fig, ax = plt.subplots(figsize=(6, 6))
ax.pie(loyalty_counts, 
       labels=loyalty_counts.index, 
       startangle=0, 
       autopct='%1.1f%%', 
       colors=custom_colors[:len(loyalty_counts)])

ax.set_title('Customer Loyalty Levels')

plt.show()
