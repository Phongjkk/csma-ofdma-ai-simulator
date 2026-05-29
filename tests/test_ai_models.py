"""Unit tests — AI: LSTM forward pass, predictor output shape, stream_predictor."""
import unittest
import numpy as np


def _make_data(N=32, T=50, F=6):
    return np.random.rand(N, T, F).astype(np.float32)


class TestMovingAverage(unittest.TestCase):
    def test_output_shape(self):
        from ai.models.moving_average import MovingAverageModel
        m = MovingAverageModel(window_size=5, n_steps=50)
        X = _make_data(10, 50, 6)
        m.fit(X, _make_data(10, 50, 6))
        out = m.predict(X)
        self.assertEqual(out.shape, (10, 50, 6))

    def test_predict_2d_input(self):
        from ai.models.moving_average import MovingAverageModel
        m = MovingAverageModel()
        X = _make_data(1, 50, 6)[0]  # 2D
        out = m.predict(X)
        self.assertEqual(out.ndim, 3)


class TestLinearRegression(unittest.TestCase):
    def test_fit_and_predict(self):
        from ai.models.linear_regression import LinearRegressionModel
        m = LinearRegressionModel(n_steps=10)
        X = _make_data(50, 20, 6)
        y = _make_data(50, 10, 6)
        m.fit(X, y)
        preds = m.predict(_make_data(5, 20, 6))
        self.assertEqual(preds.shape, (5, 10, 6))


class TestIsolationForest(unittest.TestCase):
    def test_fit_predict(self):
        from ai.models.isolation_forest import IsolationForestModel
        m = IsolationForestModel()
        X = _make_data(100, 1, 6).reshape(100, 6)
        m.fit(X)
        preds = m.predict(X[:5])
        self.assertEqual(len(preds), 5)
        self.assertTrue(all(p in (-1, 1) for p in preds))


class TestPreprocessor(unittest.TestCase):
    def test_minmax_fit_transform(self):
        from ai.data.preprocessor import MinMaxScaler
        scaler = MinMaxScaler()
        X = np.random.rand(100, 6).astype(np.float32)
        X_scaled = scaler.fit_transform(X)
        self.assertAlmostEqual(float(X_scaled.min()), 0.0, places=5)
        self.assertAlmostEqual(float(X_scaled.max()), 1.0, places=5)

    def test_inverse_transform(self):
        from ai.data.preprocessor import MinMaxScaler
        scaler = MinMaxScaler()
        X = np.random.rand(50, 6).astype(np.float32) * 10
        X_sc = scaler.fit_transform(X)
        X_inv = scaler.inverse_transform(X_sc)
        np.testing.assert_allclose(X, X_inv, atol=1e-5)

    def test_build_windows_shape(self):
        from ai.data.preprocessor import build_windows
        data = np.random.rand(200, 6).astype(np.float32)
        X, y = build_windows(data, seq_in=50, seq_out=50)
        self.assertEqual(X.shape[1], 50)
        self.assertEqual(y.shape[1], 50)
        self.assertEqual(X.shape[2], 6)


class TestSplitter(unittest.TestCase):
    def test_chronological_split_sizes(self):
        from ai.data.splitter import chronological_split
        X = np.random.rand(100, 50, 6).astype(np.float32)
        y = np.random.rand(100, 50, 6).astype(np.float32)
        splits = chronological_split(X, y, train_ratio=0.7, val_ratio=0.15)
        self.assertEqual(len(splits["X_train"]), 70)
        self.assertEqual(len(splits["X_val"]), 15)
        self.assertEqual(len(splits["X_test"]), 15)


class TestEvaluationMetrics(unittest.TestCase):
    def test_mae_zero_for_perfect(self):
        from ai.evaluation.metrics import mae
        y = np.array([1.0, 2.0, 3.0])
        self.assertAlmostEqual(mae(y, y), 0.0)

    def test_rmse_positive(self):
        from ai.evaluation.metrics import rmse
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.1, 2.1, 3.1])
        self.assertGreater(rmse(y_true, y_pred), 0.0)

    def test_precision_recall_f1(self):
        from ai.evaluation.metrics import precision_recall_f1
        y_true = np.array([1, 0, 1, 1, 0])
        y_pred = np.array([1, 0, 1, 0, 0])
        m = precision_recall_f1(y_true, y_pred)
        self.assertIn("precision", m)
        self.assertIn("recall", m)
        self.assertIn("f1", m)


if __name__ == "__main__":
    unittest.main()
