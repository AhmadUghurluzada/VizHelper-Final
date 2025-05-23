import pandas as pd
import matplotlib.pyplot as plt

# dataset used: https://www.kaggle.com/datasets/prasad22/healthcare-dataset 
data = pd.read_csv('data/healthcare_dataset.csv')
data['Billing Amount'] = pd.to_numeric(data['Billing Amount'], errors='coerce')
subset_data = data.head(50)

fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(subset_data['Age'], subset_data['Billing Amount'], color='purple', alpha=0.7)
ax.set_title('Patient Age vs Billing Amount of 50 Patients')
plt.show()
