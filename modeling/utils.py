from sklearn.metrics import classification_report, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

def check_classification_binary(model, X_train, X_test, y_train, y_test, normalize=None):
    """
    Evaluates the performance of a given model on training and testing datasets.

    The function performs the following steps:
    1. Predicts the target variable for both training and testing datasets.
    2. Displays confusion matrices for both datasets using `ConfusionMatrixDisplay`.
    3. Generates and displays classification reports for both datasets.

    Args:
        model: The trained machine learning model to evaluate.
        X_train: Training features.
        X_test: Testing features.
        y_train: Training target.
        y_test: Testing target.
        normalize (str or None, optional): This parameter is passed directly to the `normalize` argument of `ConfusionMatrixDisplay.from_estimator`. It determines how the confusion matrix is normalized. Acceptable values are:
            - None: No normalization is applied (counts are shown).
            - 'true': Normalize over the true (rows).
            - 'pred': Normalize over the predicted (columns).
            - 'all': Normalize over the whole matrix (all values sum to 1).
        See the scikit-learn documentation for more details.

    Visualization:
        - The function creates a 2x2 grid of subplots:
            - Top row: Confusion matrices for test and train datasets.
            - Bottom row: Classification reports for test and train datasets.

    Returns:
        None: The function directly displays the evaluation results.
    """

    test_pred_y = model.predict(X_test)
    train_pred_y = model.predict(X_train)

    classes = ['Terminated', 'Fulfilled']
    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(12, 4), gridspec_kw={'height_ratios': [3, 1]})

    values_format = 'd'
    if normalize != None:
        values_format = '.3f'
    cmd_test = ConfusionMatrixDisplay.from_estimator(model, X_test, y_test, display_labels=classes, normalize=normalize, values_format=values_format, cmap='Blues', ax=axes[0][0])
    axes[0][0].set_title('Test Data')
    axes[1][0].text(0, 0, classification_report(y_test, test_pred_y, target_names=classes, digits=3), verticalalignment='top', fontfamily='monospace')
    axes[1][0].axis('off')

    cmd_test = ConfusionMatrixDisplay.from_estimator(model, X_train, y_train, display_labels=classes, normalize=normalize, values_format=values_format, cmap='Greens', ax=axes[0][1])
    axes[0][1].set_title('Train Data')
    axes[1][1].text(0, 0, classification_report(y_train, train_pred_y, target_names=classes, digits=3), verticalalignment='top', fontfamily='monospace')
    axes[1][1].axis('off')

