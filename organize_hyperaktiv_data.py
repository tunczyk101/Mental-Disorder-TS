import pandas as pd
import glob
import os
import shutil

def organize_patient_data(patient_info_path, activity_data_folder, condition_folder, control_folder):
    patient_info = pd.read_csv(patient_info_path, sep=';')

    os.makedirs(condition_folder, exist_ok=True)
    os.makedirs(control_folder, exist_ok=True)

    activity_files = glob.glob(f'{activity_data_folder}/patient_activity_*.csv')

    for file in activity_files:
        patient_id = int(file.split('_')[-1].split('.')[0])

        patient_status = patient_info.loc[patient_info['ID'] == patient_id, 'ADHD'].values[0]

        if patient_status == 1:
            shutil.move(file, os.path.join(condition_folder, os.path.basename(file)))
        else:
            shutil.move(file, os.path.join(control_folder, os.path.basename(file)))
    try:
        os.rmdir(activity_data_folder)
        print(f"Directory {activity_data_folder} was removed.")
    except OSError as e:
        shutil.rmtree(activity_data_folder)
        print(f"Directory {activity_data_folder} and its contents were removed.")


if __name__ == "__main__":

    organize_patient_data(
        patient_info_path='data/hyperaktiv/patient_info.csv',
        activity_data_folder='data/hyperaktiv/activity_data',
        condition_folder='data/hyperaktiv/condition',
        control_folder='data/hyperaktiv/control'
    )
