from rocketry import Rocketry
from rocketry.conds import cron

app = Rocketry()


@app.task(cron.(minute="1"))
def run_at_minute_one():
    print("Task running at the 1st minute of the hour.")


if __name__ == "__main__":
    app.run()
