from simple_chalk import chalk

WARN_CONSUMER_DISABLED = "'{queue_name}' was disabled during runtime!"
ERROR_NO_ACTIVE_CONSUMER: str = "No non-passive consumers for '{queue_name}'!"
ERROR_PAYLOAD: str = "Payload processing error!"
INFO_PAYLOAD: str = "".join(
    [
        chalk.green("Got "),
        "{count}",
        chalk.green(" payload(s) from '"),
        "{queue_name}",
        chalk.green("'."),
    ]
)
INFO_CONSUMER_START: str = "Running `{queue_name}`..."
INFO_CONSUMER_END: str = "'{queue_name}' done in {duration:.2f}s."
