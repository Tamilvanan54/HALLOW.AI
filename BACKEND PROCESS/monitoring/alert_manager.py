def check_alerts(metrics):

    alerts = []

    if metrics["total_feedbacks"] > 50:

        alerts.append(
            "High Feedback Volume"
        )

    return alerts