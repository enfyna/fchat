from time import time


class Log:

    startup_timestamp_ms = int(time() * 1000)
    last_timestamp_ms = int(time() * 1000)
    minute_const = 60 * 1000

    @staticmethod
    def info(message):
        diff = int(time() * 1000) - Log.last_timestamp_ms
        Log.last_timestamp_ms += diff
        if diff > Log.minute_const:
            print(f"[I+{int(diff/Log.minute_const)}m] {message}")
        elif diff > 1000:
            print(f"[I+{int(diff/1000)}s] {message}")
        else:
            print(f"[I+{diff}ms] {message}")

    @staticmethod
    def warn(message):
        diff = int(time() * 1000) - Log.last_timestamp_ms
        Log.last_timestamp_ms += diff
        if diff > Log.minute_const:
            print(f"[W+{int(diff/Log.minute_const)}m] {message}")
        elif diff > 1000:
            print(f"[W+{int(diff/1000)}s] {message}")
        else:
            print(f"[W+{diff}ms] {message}")

    @staticmethod
    def error(message):
        diff = int(time() * 1000) - Log.last_timestamp_ms
        Log.last_timestamp_ms += diff
        if diff > Log.minute_const:
            print(f"[E+{int(diff/Log.minute_const)}m] {message}")
        elif diff > 1000:
            print(f"[E+{int(diff/1000)}s] {message}")
        else:
            print(f"[E+{diff}ms] {message}")

    @staticmethod
    def end():
        diff = int(time() * 1000) - Log.startup_timestamp_ms
        if diff > Log.minute_const:
            Log.info(f"Program ended in: {int(diff/Log.minute_const)}m")
        elif diff > 1000:
            Log.info(f"Program ended in: {int(diff/1000)}s")
        else:
            Log.info(f"Program ended in: {diff}ms")
