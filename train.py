import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os

# Ensure models folder exists
if not os.path.exists("models"):
    os.makedirs("models")

# Load dataset
df = pd.read_csv("data/precast_data.csv")

# Convert categorical to numeric
df["curing_type"] = df["curing_type"].map({"normal": 0, "steam": 1})

# Features and target
X = df.drop(["cycle_time"], axis=1)
y = df["cycle_time"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Model
model = xgb.XGBRegressor(
    n_estimators=400,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)

model.fit(X_train, y_train)

# Evaluation
preds = model.predict(X_test)

mae = mean_absolute_error(y_test, preds)
r2 = r2_score(y_test, preds)

print("Model Performance:")
print("MAE:", round(mae, 3))
print("R2 Score:", round(r2, 3))

# Save model
joblib.dump(model, "models/cycle_time_model.pkl")
print("Model saved successfully.")
import matplotlib.pyplot as plt

xgb.plot_importance(model)
plt.tight_layout()
plt.savefig("models/feature_importance.png")