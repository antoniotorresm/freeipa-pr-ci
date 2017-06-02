import github3
import signal
import subprocess
import time
import yaml

from prci_github import TaskQueue, AbstractJob, TaskAlreadyTaken


def quit(signum, _ignore):
    global done
    done = True


class Job(AbstractJob):
    def __call__(self):
        cmd = self.cmd.format(target_refspec=self.target)
        ok = True
        try:
            url = subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                ok = False
                url = ''
            else:
                raise

        return (ok, url,)

with open('freeipa_github.yaml') as f:
    config = yaml.load(f)

done = False
gh = github3.login(token=config['token'])
repo = gh.repository(config['user'], config['repo'])
tq = TaskQueue(repo, 'freeipa_tasks.yaml', Job)

signal.signal(signal.SIGINT, quit)
signal.signal(signal.SIGTERM, quit)
signal.signal(signal.SIGQUIT, quit)

while not done:
    tq.create_tasks_for_pulls()

    try:
        task = tq.next()
    except StopIteration:
        time.sleep(1)
        continue

    try:
        task.take('R#0')
    except TaskAlreadyTaken:
        continue

    task.execute()
