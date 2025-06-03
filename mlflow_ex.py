import mlflow
import numpy as np
import pandas as pd

import mlflow
import mlflow.sklearn

# Set remote MLflow server
mlflow.set_tracking_uri("http://185.170.112.104:5000/")
mlflow.set_experiment("linear_regression_demo")



#####Copy from MLFLOW

# Load model from MLflow
logged_model = 'runs:/597ef6ed51e34a8fb9dc16baf7409272/linear_model'
loaded_model = mlflow.pyfunc.load_model(logged_model)

# Generate new test data (like training data: X values between 0 and 2)
X_test = 2 * np.random.rand(5, 1)  # 5 new samples
df_test = pd.DataFrame(X_test, columns=["x0"])

# Predict using the loaded model
predictions = loaded_model.predict(df_test)


#####end of copy

# Output results
print("Test data:\n", df_test)
print("Predictions:\n", predictions)
