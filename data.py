# This file executes all essential functions to create the main database for regularly training the model, performing predictions with the model, and generating the necessary files for the app to function properly.


import os
import pandas as pd
from model import preprocess_data,train_xgboost_models,export_models_to_folder,load_models_from_folder,predict_and_plot,calculate_metrics_for_all_items_xgboost

# Function to create a database for Bavaria State
def process_bavaria_data(folder_path, output_file):

    # Initialize an empty DataFrame to store as a combined data
    combined_data = pd.DataFrame()

    #For selecting some particular items
    items_to_filter = ["Hof-Milch Butter mild", "Bio Aubergine 1 St", "Blumenkohl wei", "Broccoli 500g","Eisbergsalat 1 St","Galiamelone 1 St", "ja! Basmati Reis 1kg","ja! H-Milch 3,5% 1l","ja! Sonnenblumen","Karotten 1kg","Kartoffeln vorwiegend festkochend 2,5kg","Mango vorgereift 1 St","Meggle Feine Butter 250g","Orangen 2kg im Netz","Rewe Beste Wahl Eier aus Freilandhaltung 10 St","REWE Beste Wahl Feinschmecker H","REWE Bio Zucchini 500g", "Rispentomaten ca. 100g","Spitzkohl ca. 1kg","Tafeltrauben hell kernlos 500g","Zitronen 500g im Netz","Zwiebeln 2kg im Netz"]

    # Loop through files in the folder
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.csv') and len(file_name.split('_')[0]) == 10:
            try:
                # Extract date from the file name (format yyyy-mm-dd)
                date_from_filename = file_name.split('_')[0]
                file_path = os.path.join(folder_path, file_name)
                
                # Read the CSV file
                df = pd.read_csv(file_path)
                
                # Filter rows based on items_to_filter
                filtered_df = df[df.apply(lambda row: row.astype(str).str.contains('|'.join(items_to_filter)).any(), axis=1)]
                
                # Add date column
                filtered_df.insert(0, 'Date', date_from_filename)
                
                # Append filtered data to the combined DataFrame
                combined_data = pd.concat([combined_data, filtered_df], ignore_index=True)
            
            except Exception as e:
                print(f"Error processing file {file_name} in folder {folder_path}: {e}")

    # Convert the 'Date' column to datetime format for proper sorting
    combined_data['Date'] = pd.to_datetime(combined_data['Date'], format='%Y-%m-%d')

    # Sort the combined data by date
    combined_data = combined_data.sort_values(by='Date', ascending=True)

    # Save the combined data to a CSV file
    combined_data.to_csv(output_file, index=False)

    # Display the resulting combined DataFrame
    print(combined_data)
    print(f"Bavaria Database exported to '{output_file}'")


# Function to create a database for Schleswig-Holstein State
def process_schleswig_holstein_data(folder_path, output_file):

    # Initialize an empty DataFrame to store as a combined data
    combined_data = pd.DataFrame()

    #For selecting some particular items
    items_to_filter = ["Hof-Milch Butter mild", "Bio Aubergine 1 St", "Blumenkohl wei", "Broccoli 500g","Eisbergsalat 1 St","Galiamelone 1 St", "ja! Basmati Reis 1kg","ja! H-Milch 3,5% 1l","ja! Sonnenblumen","Karotten 1kg","Kartoffeln vorwiegend festkochend 2,5kg","Mango vorgereift 1 St","Meggle Feine Butter 250g","Orangen 2kg im Netz","Rewe Beste Wahl Eier aus Freilandhaltung 10 St","REWE Beste Wahl Feinschmecker H","REWE Bio Zucchini 500g", "Rispentomaten ca. 100g","Spitzkohl ca. 1kg","Tafeltrauben hell kernlos 500g","Zitronen 500g im Netz","Zwiebeln 2kg im Netz"]

    # Loop through files in the folder
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.csv') and len(file_name.split('_')[0]) == 10:
            try:
                # Extract date from the file name (format yyyy-mm-dd)
                date_from_filename = file_name.split('_')[0]
                file_path = os.path.join(folder_path, file_name)
                
                # Read the CSV file
                df = pd.read_csv(file_path)
                
                # Filter rows based on items_to_filter
                filtered_df = df[df.apply(lambda row: row.astype(str).str.contains('|'.join(items_to_filter)).any(), axis=1)]
                
                # Add date column
                filtered_df.insert(0, 'Date', date_from_filename)
                
                # Append filtered data to the combined DataFrame
                combined_data = pd.concat([combined_data, filtered_df], ignore_index=True)
            
            except Exception as e:
                print(f"Error processing file {file_name} in folder {folder_path}: {e}")

    # Convert the 'Date' column to datetime format for proper sorting
    combined_data['Date'] = pd.to_datetime(combined_data['Date'], format='%Y-%m-%d')

    # Sort the combined data by date
    combined_data = combined_data.sort_values(by='Date', ascending=True)

    # Save the combined data to a CSV file
    combined_data.to_csv(output_file, index=False)

    # Display the resulting combined DataFrame
    print(combined_data)
    print(f"Schleswig-Holstein Database exported to '{output_file}'")



# Function to create a database for Combined States
def process_combined_states_data(folders, output_file):

    # Initialize an empty DataFrame to store as a combined data
    combined_data = pd.DataFrame()

    # Items to filter
    items_to_filter = ["Hof-Milch Butter mild", "Bio Aubergine 1 St", "Blumenkohl wei", "Broccoli 500g","Eisbergsalat 1 St","Galiamelone 1 St", "ja! Basmati Reis 1kg","ja! H-Milch 3,5% 1l","ja! Sonnenblumen","Karotten 1kg","Kartoffeln vorwiegend festkochend 2,5kg","Mango vorgereift 1 St","Meggle Feine Butter 250g","Orangen 2kg im Netz","Rewe Beste Wahl Eier aus Freilandhaltung 10 St","REWE Beste Wahl Feinschmecker H","REWE Bio Zucchini 500g", "Rispentomaten ca. 100g","Spitzkohl ca. 1kg","Tafeltrauben hell kernlos 500g","Zitronen 500g im Netz","Zwiebeln 2kg im Netz"]


    # Loop through each folder and process files
    for folder_name, folder_path in folders.items():
        for file_name in os.listdir(folder_path):
            # Process only files that are CSVs and have a valid date format at the beginning
            if file_name.endswith('.csv') and len(file_name.split('_')[0]) == 10:
                try:
                    # Extract date from the file name (format yyyy-mm-dd)
                    date_from_filename = file_name.split('_')[0]
                    
                    # Full path to the file
                    file_path = os.path.join(folder_path, file_name)
                    
                    # Read the CSV file into a DataFrame
                    df = pd.read_csv(file_path)
                    
                    # Filter rows containing any of the specified items
                    filtered_df = df[df.apply(lambda row: row.astype(str).str.contains('|'.join(items_to_filter)).any(), axis=1)]
                    
                    # Add a 'Date' column with the extracted date
                    filtered_df.insert(0, 'Date', date_from_filename)
                    
                    # Add a 'State' column according to the folder name
                    filtered_df.insert(1, 'State', folder_name)
                    
                    # Append to the combined DataFrame
                    combined_data = pd.concat([combined_data, filtered_df], ignore_index=True)
                except Exception as e:
                    print(f"Error processing file {file_name} in folder {folder_name}: {e}")

    # Convert the 'Date' column to datetime format for proper sorting
    combined_data['Date'] = pd.to_datetime(combined_data['Date'], format='%Y-%m-%d')

    # Sort the DataFrame by 'Date' in ascending order
    combined_data = combined_data.sort_values(by='Date', ascending=True)

    # Save the combined data to a CSV file
    combined_data.to_csv(output_file, index=False)

    # Display the resulting combined DataFrame
    print(combined_data)
    print(f"Combined States Database exported to '{output_file}'")



# Function To Create a Master Database the App.
def Final_Items_Details(ITEM_DETAILS_EXCEL_FILE, ITEM_LIST_CSV_FILE, WEB_SCRAPING_EXCEL_FILE, FULL_ITEM_INFO_EXCEL_FILE):

    # Load Item_details.xlsx and Item_lists.csv
    item_details_data = pd.read_excel(ITEM_DETAILS_EXCEL_FILE) # Contains the basic information of all items
    item_lists_data = pd.read_csv(ITEM_LIST_CSV_FILE) # Contains the information of Predicted price from the model

    # Drop unnecessary columns from Item_lists.csv
    item_lists_data_cleaned = item_lists_data.drop(columns=['Serial_Number', 'Item_Name', 'Item_English_Name'], errors='ignore')

    # Merge Item_details.xlsx file with cleaned Item_lists.csv on the basis of Item_Code
    merged_data = pd.merge(item_details_data, item_lists_data_cleaned, how='inner', on='Item_Code', suffixes=('_details', '_lists'))

    # Load Web_Scraping.xlsx
    web_scraping_data = pd.read_excel(WEB_SCRAPING_EXCEL_FILE)

    # Drop unnecessary columns from Web_Scraping.xlsx
    cleaned_web_scraping_data = web_scraping_data.drop(columns=['Item_name_in_German', 'Item_name_in_English', 'UOM'], errors='ignore')

    # Take the last 22 rows from the cleaned Web Scraping data
    last_22_rows = cleaned_web_scraping_data.tail(22)

    # Merge the Final_Merged_Item_Details.xlsx data with the last 21 rows from Web_Scraping data on the basis of Item_Code
    final_updated_data = pd.merge(merged_data, last_22_rows, how='left', on='Item_Code', suffixes=('_final', '_webscraping'))

    #Save the final updated file
    final_updated_data.to_excel(FULL_ITEM_INFO_EXCEL_FILE, index=False)

    return FULL_ITEM_INFO_EXCEL_FILE



if __name__ == "__main__":

    # Create a database for Bavaria State
    Bavaria_path = "Datasets/Raw_Data/Datapoints/Bavaria/"
    Bavaria_file = "Datasets/Raw_Data/grocery_items_bavaria.csv"
    process_bavaria_data(Bavaria_path, Bavaria_file)


    # Create a database for Schleswig Holstein State
    Holstein_path = "Datasets/Raw_Data/Datapoints/Schleswig-Holstein/"
    Holstein_file = "Datasets/Raw_Data/grocery_items_Schleswig_Holstein.csv"
    #process_schleswig_holstein_data(Holstein_path, Holstein_file)


    # Create a database for Combined State
    folders = {
        "Bavaria": "Datasets/Raw_Data/Datapoints/Bavaria/",
        "Schleswig-Holstein": "Datasets/Raw_Data/Datapoints/Schleswig-Holstein/"
    }
    combined_states_file = "Datasets/Raw_Data/grocery_items_two_state.csv"
    #process_combined_states_data(folders, combined_states_file)


    # Take Bavaria Database to train model
    grocery_data = pd.read_csv('Datasets/Raw_Data/grocery_items_bavaria.csv')
    grocery_data.rename(columns={'name': 'Items'}, inplace=True)

    # Delete old 'Item_lists.csv' file if exists 
    csv_file_path = "Datasets/Model_Output/Price_Prediction/Item_lists.csv"
    if os.path.exists(csv_file_path):
        os.remove(csv_file_path)
        print(f"Existing file {csv_file_path} has been deleted.")

    # Preprocess the database of Bavaria
    print("Preprocessing data...")
    processed_data = preprocess_data(grocery_data)

    # Train XGBoost model
    print("Training models...")
    xgboost_models = train_xgboost_models(processed_data, lags=30)

    # Export the trained model to a folder
    models_folder = "Model/XGBoost"
    export_models_to_folder(xgboost_models, models_folder)

    # Load the trained model from the folder
    print("Loading models...")
    loaded_models = load_models_from_folder(models_folder)

    # Predict Future Price and Plot for a Specific Item
    item_names = [
        "Allgäuer Hof-Milch Butter mild gesäuert 250g",
        "Bio Aubergine 1 Stück",
        "Blumenkohl weiß 1 Stück",
        "Broccoli 500g",
        "Eisbergsalat 1 Stück",
        "Galiamelone 1 Stück",
        "Karotten 1kg",
        "Kartoffeln vorwiegend festkochend 2,5kg",
        "Mango vorgereift 1 Stück",
        "Meggle Feine Butter 250g",
        "Orangen 2kg im Netz",
        "REWE Beste Wahl Feinschmecker Hähnchen 1200g",
        "REWE Bio Zucchini 500g",
        "Rewe Beste Wahl Eier aus Freilandhaltung 10 Stück",
        "Rispentomaten ca. 100g",
        "Spitzkohl ca. 1kg",
        "Tafeltrauben hell kernlos 500g",
        "Zitronen 500g im Netz",
        "Zwiebeln 2kg im Netz",
        "ja! Basmati Reis 1kg",
        "ja! H-Milch 3,5% 1l",
        "ja! Sonnenblumenöl 1l"
    ]

    # Loop through the item names and call predict_and_plot for each
    for item_name in item_names:
        print(f"Predicting and plotting for: {item_name}")
        predict_and_plot(item_name, loaded_models, processed_data)


    # Calculate Error Metrics for all items
    print("Calculating metrics for all items using XGBoost...")
    metrics_df = calculate_metrics_for_all_items_xgboost(loaded_models, processed_data, lags=30, test_steps=30)

    # To Display the Error Metrics
    print("\nError Metrics for All Items:")
    print(metrics_df)

    # Save the Error Metrics to a CSV file
    error_metrics_path = "Datasets/Model_Output/Model_Performance/error_metrics_all_items_xgboost.csv"
    metrics_df.to_csv(error_metrics_path, index=False)
    print(f"Results of Error Metrics exported to '{error_metrics_path}'")


    # To create a Master Database for the App.
    ITEM_DETAILS_EXCEL_FILE = "Datasets/Raw_Data/Item_details.xlsx"
    ITEM_LIST_CSV_FILE = 'Datasets/Model_Output/Price_Prediction/Item_lists.csv'
    WEB_SCRAPING_EXCEL_FILE = 'Datasets/Web_Scraping/Web_Scraping.xlsx'
    FULL_ITEM_INFO_EXCEL_FILE = 'static/Files/Full_Item_Info.xlsx'

    result_path = Final_Items_Details(ITEM_DETAILS_EXCEL_FILE, ITEM_LIST_CSV_FILE, WEB_SCRAPING_EXCEL_FILE, FULL_ITEM_INFO_EXCEL_FILE)
    print(f"App's Master Database exported to '{result_path}'")


