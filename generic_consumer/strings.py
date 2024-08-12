from simple_chalk import chalk

WARN_CONSUMER_DISABLED: str = "".join(
    [
        chalk.yellow("'"),
        "{queue_name}",
        chalk.yellow("' was disabled during runtime!"),
    ]
)
ERROR_NO_ACTIVE_CONSUMER: str = "No non-passive consumers for '{queue_name}'!"
ERROR_PAYLOAD: str = chalk.yellow("Payload processing error!")
INFO_PAYLOAD: str = "".join(
    [
        chalk.green("Got "),
        "{count}",
        chalk.green(" payload(s) from '"),
        "{queue_name}",
        chalk.green("'."),
    ]
)
INFO_CONSUMER_RUN: str = chalk.gray.dim(
    "\r\nRunning `{0}`...\r\n",
)
INFO_CONSUMER_RUN: str = INFO_CONSUMER_RUN.format(
    chalk.bold("{queue_name}"),
)
