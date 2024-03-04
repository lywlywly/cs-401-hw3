from datetime import datetime, timedelta


def percentage_outgoing_traffic_bytes(metrics):
    n_bytes_sent = metrics["net_io_counters_eth0-bytes_sent"]
    n_bytes_received = metrics["net_io_counters_eth0-bytes_recv"]

    return n_bytes_sent * 100.0 / (n_bytes_sent + n_bytes_received)


def percentage_memory_caching_content(metrics):
    memory_buffer = metrics["virtual_memory-buffers"]
    memory_cached = metrics["virtual_memory-cached"]
    memory_used = metrics["virtual_memory-total"]

    return 100 * (memory_buffer + memory_cached) / memory_used


def moving_avg_cpu(metrics: dict, context: dict):
    result = {}
    metrics_timestamp = metrics["timestamp"]
    metrics_datetime = datetime.fromisoformat(metrics_timestamp)
    one_minute_ago_datetime = metrics_datetime - timedelta(minutes=1)

    for cpu_index in range(128):
        cpu_key = f"cpu_percent-{cpu_index}"
        current_percent = metrics.get(cpu_key)
        if current_percent is None:
            break

        percents_last_minute = [
            (percent, datetime)
            for percent, datetime in context.env.get(cpu_key, [])
            if datetime > one_minute_ago_datetime
        ]

        percents_last_minute.append((current_percent, metrics_datetime))
        context.env[cpu_key] = percents_last_minute

        moving_average = sum(percent for percent, _ in percents_last_minute) / len(
            percents_last_minute
        )
        result[f"moving_average_{cpu_key}"] = moving_average

    return result


def handler(metrics: dict, context=None) -> dict:
    result: dict = {}
    result["percentage_outgoing_bytes"] = percentage_outgoing_traffic_bytes(metrics)
    result["percentage_memory_caching"] = percentage_memory_caching_content(metrics)
    result.update(moving_avg_cpu(metrics, context))
    result["datetime"] = datetime.now().isoformat()

    return result


# test dummy context class
class Context:
    def __init__(self) -> None:
        self.env = {}


if __name__ == "__main__":
    # test client
    import redis
    import json
    from time import sleep

    redis_connection = redis.Redis(
        host="10.244.0.1", port=6379, db=0, decode_responses=True
    )
    context = Context()
    for _ in range(100):
        metrics = json.loads(redis_connection.get("metrics"))
        result = handler(metrics, context)
        print(result)
        sleep(1)
