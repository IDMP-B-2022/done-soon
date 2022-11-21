import argparse
import logging
import os
import signal
import sys
import time
from multiprocessing import Process, cpu_count
from threading import Lock

import psutil
from rich.logging import RichHandler
from done_soon.data_generation import data_gen_worker


fh = logging.FileHandler("generate_data.log")
fh.setLevel(logging.DEBUG)
fh_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(processName)s : %(message)s")
fh.setFormatter(fh_formatter)
rh = RichHandler(markup=True)
rh.setLevel(logging.DEBUG)
rh_formatter = logging.Formatter("%(message)s", datefmt="%X")
rh.setFormatter(rh_formatter)
logger = logging.getLogger("generate_data")
logger.addHandler(fh)
logger.addHandler(rh)
logger.setLevel(logging.DEBUG)

WORKERS_LOCK = Lock()
WORKERS = {}

class ControllerArgs(data_gen_worker.WorkerArgs):
    jobs: int


def handle_interrupt_controller(*_):
    print()
    close_workers()
    sys.exit(1)


def close_workers():
    WORKERS_LOCK.acquire(blocking=True)
    for worker in WORKERS.values():
        worker_process = psutil.Process(worker.pid)
        for child in worker_process.children(recursive=True):
            logger.debug("Killing child (%d) of %d", child.pid, worker.pid)
            child.terminate()
        logger.debug("Killing %d", worker.pid)
        worker.terminate()
        worker.join()
        worker.close()
    WORKERS_LOCK.release()


def respawn_dead_workers(args):
    WORKERS_LOCK.acquire(blocking=False)

    global WORKERS
    cpus_to_reuse = []
    for i, worker in WORKERS.items():
        if not worker.is_alive():
            logger.error("%s is no longer alive", worker.name)
            worker.close()
            cpus_to_reuse.append(i)

    WORKERS = {i: worker for i, worker in WORKERS.items() if i not in cpus_to_reuse}

    for i in cpus_to_reuse:
        p = Process(target=lambda: data_gen_worker.start_worker(args))
        WORKERS[i] = p
        p.start()
        logger.info("Starting new worker %s", p.name)
        os.system(f"taskset -p -c {i} {p.pid} >/dev/null 2>&1")

    WORKERS_LOCK.release()


def parse_args():
    parser = argparse.ArgumentParser(
        description='Spawns processes to generate/store data')
    controller = parser.add_argument_group('Controller Arguments',
                                             'Arguments to direct the spawning of processes.')
    controller.add_argument('--jobs', help='Number of subprocesses to spawn',
                                  default=cpu_count(), type=int)
    worker_group = parser.add_argument_group('Worker Arguments',
                                             'Arguments for each worker process to use.')
    data_gen_worker.add_args(worker_group)

    args = parser.parse_args(namespace=ControllerArgs())
    print(args)
    return args

def main():
    args = parse_args()

    signal.signal(signal.SIGINT, handle_interrupt_controller)

    WORKERS_LOCK.acquire(blocking=True)

    for i in range(args.jobs):
        p = Process(target=lambda: data_gen_worker.start_worker(args))
        WORKERS[i] = p
        p.start()
        logger.info("Starting new worker: %s", p.name)
        os.system(f"taskset -p -c {i} {p.pid} >/dev/null 2>&1")

    WORKERS_LOCK.release()
    while True:
        time.sleep(10)
        respawn_dead_workers(args)


if __name__ == "__main__":
    main()
