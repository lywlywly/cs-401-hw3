from datetime import datetime

from severless_function import (
    moving_avg_cpu,
    percentage_memory_caching_content,
    percentage_outgoing_traffic_bytes,
)


def handler(metrics: dict, context=None) -> dict:
    result: dict = {}
    result["percentage_outgoing_bytes"] = percentage_outgoing_traffic_bytes(metrics)
    result["percentage_memory_caching"] = percentage_memory_caching_content(metrics)
    result.update(moving_avg_cpu(metrics, context))
    result["datetime"] = datetime.now().isoformat()

    return result
