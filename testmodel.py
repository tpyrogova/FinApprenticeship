import numpy as np
from sklearn.linear_model import LinearRegression
import mlflow
import mlflow.sklearn

# Set remote MLflow server
mlflow.set_tracking_uri("http://185.170.112.104:5000/")
mlflow.set_experiment("linear_regression_demo")


# Generate random data
X = 2 * np.random.rand(100, 1)
y = 4 + 3 * X + np.random.randn(100, 1)

# Train the model
model = LinearRegression()
model.fit(X, y)

# Log to remote MLflow
with mlflow.start_run():
    mlflow.log_param("fit_intercept", model.fit_intercept)
    mlflow.log_metric("slope", model.coef_[0][0])
    mlflow.log_metric("intercept", model.intercept_[0])
    mlflow.sklearn.log_model(model, "linear_model")
