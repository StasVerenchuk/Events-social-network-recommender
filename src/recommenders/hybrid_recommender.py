"""
Learning-to-Rank модуль (Python 3.10)

• підтримує декілька алгоритмів («svm», «mlp», «nb», «rf»);
• будує матриці ознак на основі словника simscores_across_features;
• зберігає граф важливості ознак у figures/feature_importance/{partition}.png
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_recall_fscore_support
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier
from sklearn.svm import LinearSVC


class LearningToRank:
    """Об’єднує кілька «базових» фіч у мета-класіфікатор (L2R)."""

    def __init__(self) -> None:
        # ── каталог для графіків
        Path("figures/feature_importance").mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    #  основний пайплайн: train / test та оцінка
    # ------------------------------------------------------------------ #
    def learn(
        self,
        simscores: Dict[str, Dict[str, Dict[str, float]]],
        test_events: List[str],
        all_members_rsvp: Dict[str, List[str]],
        test_members: List[str],
        log_fh,  # відкритий файл-хендл для логів
        algo_list: List[str],
        n_members: int,
        partition_number: int,
    ) -> None:
        """
        • Формує матрицю ознак X і ціль y (1 – відвідав, 0 – ні);
        • 80 % користувачів → train, 20 % → test;
        • Навчає обрані алгоритми, друкує Precision/Recall/F-score;
        • Будує bar-chart важливості ознак (RF / LinearSVC).
        """

        # -------------------- 1. побудова X_train, y_train --------------------
        feature_names = list(simscores.keys())
        train_size = int(0.8 * n_members)

        X_train, y_train = self._build_matrix(
            test_members[:train_size],
            test_events,
            simscores,
            all_members_rsvp,
        )
        X_test, y_test = self._build_matrix(
            test_members[train_size:],
            test_events,
            simscores,
            all_members_rsvp,
        )

        # -------------------- 2. тренування / оцінка --------------------------
        if "svm" in algo_list:
            self._run_classifier(
                clf=LinearSVC(),
                name="SVM",
                X_train=X_train,
                y_train=y_train,
                X_test=X_test,
                y_test=y_test,
                feature_names=feature_names,
                partition_number=partition_number,
                subplot_pos=211,
                log_fh=log_fh,
            )

        if "mlp" in algo_list:
            self._run_classifier(
                clf=MLPClassifier(max_iter=500, random_state=42),
                name="MLP",
                X_train=X_train,
                y_train=y_train,
                X_test=X_test,
                y_test=y_test,
                log_fh=log_fh,
            )

        if "nb" in algo_list:
            self._run_classifier(
                clf=GaussianNB(),
                name="Naive Bayes",
                X_train=X_train,
                y_train=y_train,
                X_test=X_test,
                y_test=y_test,
                log_fh=log_fh,
            )

        if "rf" in algo_list:
            self._run_classifier(
                clf=RandomForestClassifier(
                    n_estimators=50, n_jobs=-1, random_state=15325
                ),
                name="Random Forest",
                X_train=X_train,
                y_train=y_train,
                X_test=X_test,
                y_test=y_test,
                feature_names=feature_names,
                partition_number=partition_number,
                subplot_pos=212,
                log_fh=log_fh,
            )

        # -------------------- 3. збереження графіку --------------------------
        if any(algo in algo_list for algo in ("svm", "rf")):
            plt.tight_layout()
            out_path = (
                f"figures/feature_importance/{partition_number}_partition.png"
            )
            plt.savefig(out_path)
            plt.close()

    # ====================================================================== #
    # ↓↓↓ допоміжні функції ↓↓↓
    # ====================================================================== #
    @staticmethod
    def _build_matrix(
        members: List[str],
        events: List[str],
        simscores: Dict[str, Dict[str, Dict[str, float]]],
        rsvp: Dict[str, List[str]],
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Створює X, y для заданого підмножини користувачів."""
        features = []
        labels = []
        for feature in simscores:  # по кожній базовій моделі
            col = [
                simscores[feature][member][event]
                for member in members
                for event in events
            ]
            features.append(col)

        for member in members:
            labels.extend(
                1 if event in rsvp.get(member, []) else 0 for event in events
            )

        X = np.column_stack(features)
        y = np.asarray(labels)
        return X, y

    def _run_classifier(
        self,
        clf,
        name: str,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        log_fh,
        feature_names: List[str] | None = None,
        partition_number: int | None = None,
        subplot_pos: int | None = None,
    ) -> None:
        """Навчання, оцінка та (опціонально) граф важливості ознак."""
        clf.fit(X_train, y_train)
        preds = clf.predict(X_test)
        pr, rc, f1, _ = precision_recall_fscore_support(
            y_test, preds, labels=[0, 1]
        )

        print(f"{name:<12} →  Precision {pr[1]:.3f}  Recall {rc[1]:.3f}  F1 {f1[1]:.3f}")
        log_fh.write(
            f"{name:<12} →  Precision {pr[1]:.3f}  Recall {rc[1]:.3f}  F1 {f1[1]:.3f}\n"
        )
        log_fh.flush()

        # ---- важливість ознак (тільки SVM (coef_) чи RF (feature_importances_)) ----
        if feature_names and partition_number and subplot_pos:
            if hasattr(clf, "coef_"):
                importances = clf.coef_.ravel()
            elif hasattr(clf, "feature_importances_"):
                importances = clf.feature_importances_
            else:
                return

            ax = plt.subplot(subplot_pos)
            ax.set_title(f"{name} – feature importance")
            bars = ax.bar(
                np.arange(len(importances)),
                importances,
                color="steelblue",
            )
            ax.set_xticks(np.arange(len(importances)))
            ax.set_xticklabels(feature_names, rotation=60, ha="right")
            ax.bar_label(bars, fmt="%.2f")
