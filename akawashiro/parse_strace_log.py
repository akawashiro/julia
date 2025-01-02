import argparse
from dataclasses import dataclass
import logging
import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches

logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.DEBUG,
)


@dataclass
class Process:
    pid: int
    start_time: int
    end_time: int
    program: str


def plot_processes(processes: list[Process], image_file: str) -> None:
    fig = plt.figure()
    fig.savefig(image_file)


def generate_trace_json(processes: list[Process]) -> str:
    processes = list(filter(lambda p: p.end_time > p.start_time, processes))

    trace = []
    offset_time = 1 << 32

    dummy_pids: dict[str, int] = {}

    for p in processes:
        s = p.start_time * 1000
        e = p.end_time * 1000
        if p.program not in dummy_pids:
            dummy_pids[p.program] = len(dummy_pids)
        dummy_pid = dummy_pids[p.program]

        offset_time = min(offset_time, s)
        trace.append(
            {
                "name": p.program,
                "cat": p.program,
                "ts": s,
                "ph": "B",
                "pid": dummy_pid,
                "tid": p.pid,
                "args": {},
            }
        )
        trace.append(
            {
                "name": p.program,
                "cat": p.program,
                "ph": "E",
                "ts": e,
                "pid": dummy_pid,
                "tid": p.pid,
                "args": {},
            }
        )
    for t in trace:
        t["ts"] -= offset_time
    trace_json = {
        "traceEvents": trace,
        "displayTimeUnit": "ms",
    }
    return json.dumps(trace_json, indent=4)


def main(log_file: str, output_json: str, output_image: str) -> None:
    # pid -> Process
    processes: dict[int, Process] = {}
    with open(log_file, "r") as f:
        for line in f:
            line = line.replace("(", " ").replace('"', " ")
            ws = line.split()
            if len(ws) > 2 and ws[2] == "execve":
                p = Process(
                    pid=int(ws[0]),
                    start_time=int(ws[1]),
                    end_time=(1 << 32),
                    program=ws[3],
                )
                processes[p.pid] = p
            if len(ws) > 2 and ws[2] == "exit" or ws[2] == "exit_group":
                if int(ws[0]) in processes:
                    processes[int(ws[0])].end_time = int(ws[1])
                else:
                    logging.warning(f"pid {int(ws[0])} not found")

    legitimate_processes: list[Process] = []
    for p in processes.values():
        if p.end_time == (1 << 32):
            logging.warning(f"pid {p.pid} {p.program} has no end time")
        else:
            legitimate_processes.append(p)
    trace = generate_trace_json(legitimate_processes)
    with open(output_json, "w") as f:
        f.write(trace)

    plot_processes(legitimate_processes, output_image)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse strace log")
    parser.add_argument("--log", type=str, help="strace log file", required=True)
    parser.add_argument(
        "--output_json", type=str, help="output json file", required=True
    )
    parser.add_argument(
        "--output_image", type=str, help="output plot file", required=True
    )
    args = parser.parse_args()
    main(args.log, args.output_json, args.output_image)
