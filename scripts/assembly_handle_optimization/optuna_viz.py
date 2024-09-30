import pickle
import optuna

# Load the Optuna study from the pickle file
with open('/Users/matt/Desktop/optuna_testing/study_trial_resume_250.pkl', 'rb') as f:
    loaded_study = pickle.load(f)

# Define the SQLite database URL
sqlite_url = "sqlite:////Users/matt/Desktop/optuna_testing/trial_250_sql.db"

# Set up the RDBStorage for SQLite
storage = optuna.storages.RDBStorage(url=sqlite_url)

# Create a new study in SQLite with the same study name as the loaded study
new_study = optuna.create_study(storage=storage, direction=loaded_study.direction)

# Loop through each trial from the loaded study and add it to the new SQLite-based study
for trial in loaded_study.trials:
    new_study.add_trial(trial)
