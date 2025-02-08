import os
import pandas as pd
import pickle
from datetime import timedelta
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Mapping of Item Name to Item Code
ITEM_CODE_MAPPING = {
    "Allgäuer Hof-Milch Butter mild gesäuert 250g": "101",
    "Bio Aubergine 1 Stück": "201",
    "Blumenkohl weiß 1 Stück": "301",
    "Broccoli 500g": "401",
    "Eisbergsalat 1 Stück": "501",
    "Galiamelone 1 Stück": "601",
    "Karotten 1kg": "701",
    "Kartoffeln vorwiegend festkochend 2,5kg": "801",
    "Mango vorgereift 1 Stück": "901",
    "Meggle Feine Butter 250g": "1001",
    "Orangen 2kg im Netz": "1101",
    "REWE Beste Wahl Feinschmecker Hähnchen 1200g": "1201",
    "REWE Bio Zucchini 500g": "1301",
    "Rewe Beste Wahl Eier aus Freilandhaltung 10 Stück": "1401",
    "Rispentomaten ca. 100g": "1501",
    "Spitzkohl ca. 1kg": "1601",
    "Tafeltrauben hell kernlos 500g": "1701",
    "Zitronen 500g im Netz": "1801",
    "Zwiebeln 2kg im Netz": "1901",
    "ja! Basmati Reis 1kg": "2001",
    "ja! H-Milch 3,5% 1l": "2101",
    "ja! Sonnenblumenöl 1l": "2201"
}

# Mapping of Item Code to Item English Name
ITEM_CODE_TO_ENGLISH_NAME = {
    "101": "Soured Butter",
    "201": "Eggplant",
    "301": "White Cauliflower",
    "401": "Broccoli",
    "501": "Iceberg Lettuce",
    "601": "Galia Melon",
    "701": "Carrots",
    "801": "Potatoes",
    "901": "Mango",
    "1001": "Fine Butter",
    "1101": "Oranges",
    "1201": "Chicken",
    "1301": "Zucchini",
    "1401": "Eggs",
    "1501": "Tomatoes",
    "1601": "Cabbage",
    "1701": "Table Grapes",
    "1801": "Lemons",
    "1901": "Onions",
    "2001": "Basmati Rice",
    "2101": "Milk 3.5%",
    "2201": "Sunflower Oil"
}


# Dataset preprocessing function
def preprocess_data(data):

    data['Date'] = pd.to_datetime(data['Date'])
    data = data.groupby(['Items', 'Date'], as_index=False)['price'].mean()

    all_items = []
    for item in data['Items'].unique():
        item_data = data[data['Items'] == item]
        item_data = item_data.set_index('Date').asfreq('D')  # Fill in missing dates
        item_data['Items'] = item
        item_data['price'] = item_data['price'].fillna(method='ffill') # Fill in prices
        all_items.append(item_data)

    return pd.concat(all_items).reset_index()


# Create lagged features for time series data
def create_lagged_features(data, lags=30):
    data = data.copy()
    for lag in range(1, lags + 1):
        data[f'lag_{lag}'] = data['price'].shift(lag)
    return data.dropna()


# Train XGBoost models for all items
def train_xgboost_models(data, lags=30):
    models = {}
    for item in data['Items'].unique():
        try:
            item_data = data[data['Items'] == item].set_index('Date')
            item_data = create_lagged_features(item_data, lags=lags)
            
            X = item_data.drop(columns=['price', 'Items'])
            y = item_data['price']

            model = XGBRegressor(objective='reg:squarederror', n_estimators=100)
            model.fit(X, y)
            models[item] = model
            print(f"Trained XGBoost model for: {item}")
        except Exception as e:
            print(f"Could not train model for {item}: {e}")
    return models


# Export models to a folder
def export_models_to_folder(models, folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)  # Create the folder if it doesn't exist
    filepath = os.path.join(folder_name, "xgboost_models.pkl")
    with open(filepath, 'wb') as f:
        pickle.dump(models, f)
    print(f"Models exported to folder: {folder_name}")


# Load models from a folder
def load_models_from_folder(folder_name):
    filepath = os.path.join(folder_name, "xgboost_models.pkl")
    with open(filepath, 'rb') as f:
        models = pickle.load(f)
    print(f"Models successfully loaded from folder: {folder_name}")
    return models


# Predict and plot
def predict_and_plot(item_name, models, data, steps=90, lags=30):
    if item_name not in models:
        print(f"No model found for item: {item_name}")
        return

    plot_path="static/images"
    csv_file="Datasets/Model_Output/Price_Prediction/Item_lists.csv" # Path to save model predicted values

    item_folder = os.path.join(plot_path, 'Item_Plot')
    
    if not os.path.exists(item_folder):
        os.makedirs(item_folder)

    model = models[item_name]
    item_data = data[data['Items'] == item_name].set_index('Date')
    item_data = create_lagged_features(item_data, lags=lags)
    
    # Use the last `lags` values for prediction
    recent_data = item_data.iloc[-1, 2:].values.reshape(1, -1)

    forecast = []
    for _ in range(steps):
        pred = model.predict(recent_data)[0]
        forecast.append(pred)
        
        # Shift the recent data to include the new prediction
        recent_data = np.roll(recent_data, -1)
        recent_data[0, -1] = pred

    future_dates = pd.date_range(start=item_data.index[-1] + timedelta(days=1), periods=steps)

    # Smooth the historical prices
    smoothed_prices = gaussian_filter1d(item_data['price'], sigma=2)
    smoothed_forecast = gaussian_filter1d(forecast, sigma=2)

    # Combine historical and forecast data for plotting
    combined_dates = list(item_data.index) + list(future_dates)
    combined_values = np.concatenate([smoothed_prices, smoothed_forecast])

    # Ensure both lists have the same length
    min_length = min(len(combined_dates), len(combined_values))
    combined_dates = combined_dates[:min_length]
    combined_values = combined_values[:min_length]

    # Save forecast to CSV file
    price_for_tomorrow = forecast[1]
    price_after_7_days = forecast[7] if len(forecast) > 7 else None
    price_after_1_month = forecast[30] if len(forecast) > 30 else None

    item_code = ITEM_CODE_MAPPING.get(item_name, "Unknown")
    item_english_name = ITEM_CODE_TO_ENGLISH_NAME.get(item_code, "Unknown")

    summary_data = {
        "Serial_Number": [len(pd.read_csv(csv_file)) + 1 if os.path.exists(csv_file) else 1],
        "Item_Code": [item_code],
        "Item_Name": [item_name],
        "Item_English_Name": [item_english_name],
        "Price_for_Tomorrow": [price_for_tomorrow],
        "Price_After_7_Days": [price_after_7_days],
        "Price_After_1_Month": [price_after_1_month]
    }

    summary_df = pd.DataFrame(summary_data)

    # Append to CSV if file exists, otherwise create
    if os.path.exists(csv_file):
        summary_df.to_csv(csv_file, mode='a', header=False, index=False)
    else:
        summary_df.to_csv(csv_file, index=False)

    print(f"Item's information added to {csv_file}")
    

    # Plot the forcasting for an item
    plt.figure(figsize=(12, 6))
    plt.plot(combined_dates, combined_values, label="Current Price", linewidth=3, color="forestgreen") # Show Current Values
    plt.plot(future_dates, smoothed_forecast, label="Prediction (Next 90 Days)", linewidth=3, linestyle='-', color='cornflowerblue') # Show future values
    plt.title(f"Changes in {item_english_name} Prices Over The Years.", fontsize=16)
    plt.ylabel("Price (€)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    # Save Item's plot for the app
    plot_file = os.path.join(item_folder, f"{item_code.replace(' ', '_')}.png")
    plt.savefig(plot_file)
    plt.close()
    print(f"Plot saved to {plot_file}")


# Function to calculate error metrics for all items using XGBoost
def calculate_metrics_for_all_items_xgboost(models, data, lags=30, test_steps=90):
    metrics = []  # List to store metrics for each item

    for item_name in data['Items'].unique():
        if item_name not in models:
            print(f"No model found for item: {item_name}")
            continue
        
        try:
            # Extract data for the item
            item_data = data[data['Items'] == item_name].set_index('Date')
            item_data = create_lagged_features(item_data, lags=lags)

            # Split the data into train and test
            train = item_data[:-test_steps]
            test = item_data[-test_steps:]

            # Prepare the feature matrix and target variable
            X_train = train.drop(columns=['price', 'Items'])
            y_train = train['price']
            X_test = test.drop(columns=['price', 'Items'])
            y_test = test['price']

            # Use the pre-trained model
            model = models[item_name]

            # Predict the test period
            y_pred = model.predict(X_test)

            # Calculate error metrics
            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100

            # Append metrics to the list
            metrics.append({
                'Item': item_name,
                'MAE': mae,
                'MSE': mse,
                'RMSE': rmse,
                'MAPE': mape
            })

            print(f"Metrics calculated for: {item_name}")
        
        except Exception as e:
            print(f"Could not calculate metrics for {item_name}: {e}")
        
    # Convert metrics to DataFrame
    metrics_df = pd.DataFrame(metrics)
    return metrics_df


